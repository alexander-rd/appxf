# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Basic Storage Behavior '''

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Protocol, runtime_checkable, overload
from copy import deepcopy
from inspect import isabstract

from appxf.logging import logging
from .meta_data import MetaData

# TODO: Collect an inventory. __init__ of this base class shall collect all
# __init__'s and be able to report (a) all locations (as a list) and (b) all
# locations including all files (map with key being location and value being
# list of files).

# TODO RELEASE: StorageLocation should support some sync_with_timestamps().
# That returns True when the StorageLocation can ensure that new files will
# always have a newer timestamp. For example: by delaying a write operation or
# repeating it when the resulting time stamp did not change.

# TODO: document @overload as a good habit to give hints on kwarg names on
# functions like get_factory.


class AppxfStorageError(Exception):
    ''' Error in storage handling '''


class AppxfStorageDerivationRawBaseError(AppxfStorageError):
    ''' Error during derivation from this class '''
    def __init__(
            self,
            message: str = (
                'You have to provide all raw handling functions (exists, '
                '_load, _store) or none. '
                'Rationale: Storage can otherwisde not safely identify '
                'the base storage in a derivation hierachy. '
                'The base storage class gets the final storage instance '
                'registered also such that syncing between two base '
                'storages (1) covers all generated storages with (2) the '
                'correct storage method.'),
            **kwargs
            ):
        super().__init__(message, **kwargs)


class AppxfStorageWarning(Warning):
    ''' Warning on storage handling '''


class Storage(ABC):
    ''' Providing storage behavior

    Main purpose of this class is store() and load() as an abstraction to
    store/load python objects. Any class dependent on Storage can then be used
    in combination with various storage options like:
      * local file storage
      * storage on FTP
      * encrypted storage (local or FTP)
      * storage in RAM

    The Storage class includes:
      * a strict location concept to protect from defining the same storage in
        an application
      * a custom meta data concept to support file synchronization
      * support for shared storage where the user that has written the data may
        be relevant
      * support for modules that may need to generate multiple storage items.
        In this case, a Storage.Factory function is generated from the Storage
        class that can be passed to the module.
      * synchronization of data via manually defined pairs or the
        Storage.Factory that can return all registered storages of a location.
      * intended extention of the behavior by overwriting one of the following
        three steps:
          1) Adding a way of storing raw data: _store() and _load(). Examples:
             LocalStorage, RamStorage. exist() also belongs to this group of
             abstracted functions.
          2) Adapting the transformation from the python data type to the raw
             data type like bytes in case of file storage: _convert_to_raw(),
             _convert_from_raw(). Example: SerializingStorage as reusable class
             between this Storage class and LocalStorage.
          3) Operations on the original python data type if the Storage becomes
             specific to a set of python datatypes: store() and load().
        When deriving from Storage directly, _store(), _load() and exist() must
        be provided. When overloading or composing with this class or a
        derivative, always consider calling the existing functions for steps
        (1), (2) and (3) to maintain their purpose.
      * Storage works together with the Storable class. While Storage handles
        _how_ information is stored, Storable handles _what_ information is
        stored. The interactions are based on:
         * The Storable get's a Storage class upon construction
         * The Storable obtains a Storage object and sets the name
         * The specific Storable defines a _set_state() and _get_state while
           the abstract Storable realizes a store(), load() and exist() based
           on the corresponding Storage methods to combine the "what to store"
           with the "how to store".
    '''

    # ##################
    # CLASS ATTRIBUTES
    # /

    # The registry of storages differentiates the storage item name and a
    # unique storage location (like folders of URL+path). The registry has
    # therefore a first level (the location) and a second level (the storage
    # item's name). Both are provided during construction:
    _storage_registry: dict[str, dict[str, Storage]] = {}

    # Context is a weirdo feature that should not be used in applications but
    # is required during testing. If two or more application instances need to
    # be tested, each one needs it's different storage context if shared
    # storage is employed. The underlying problem is the following:
    #   * SharedStorage accesses the same physical location
    #   * While the SharedStorage is different since a different user will
    #     access, the underlying physical storage is not.
    #   * Problem 1: After constructing SharedStorage for user A which uncludes
    #     construction of the base storage. The construction of SharedStorage
    #     for user B wil fail since it will try to construct the same base
    #     storage that is already registered.
    #   * Problem 2: For consistent unregistering and sync access, the base
    #     storage will have the SharedStorage registered. If multiple users
    #     access the same base storage: which SharedStorage would be linked?
    # The problem is resolved by applying a context to all storages via this
    # variable:
    _context: str = ''
    # Whenever the application instances are accessed, in particular during
    # construction, the context will be set via switch_context(). Storage
    # objects will know their context such that context switching would not be
    # required as long as not storage objects are created. To ensure safe
    # operations disable_context() can be used, resulting in errors if new
    # storage objects would be generated.
    #
    # The following variable would store registry backup based on the context:
    _context_registry_backup: dict[str, dict[str, dict[str, Storage]]] = {}
    # And the following is set in switch_context when switching to context="".
    _context_locked = False

    # Storage class will remember derived classes to handle context switching
    # and resets properly. Note that this list remains accessible from all
    # classes as long as it is not replaced upon construction of a new class.
    # Only non-abstract classes will be added.
    _storage_class_registry: list[type[Storage]] = []

    # Control meta data handling on class level. Can be overwritten also on
    # instance level.
    _meta_data_enabled = False
    # Logger for this class (deriving class is overwritten in
    # __init_subclass__:
    log = logging.getLogger(f'{__name__}.Storage')

    # ####################
    # FACTORY BEHAVIOR
    # /
    def __init_subclass__(cls):
        ''' Deriving class providing additional class information
        '''
        cls.log = logging.getLogger(
            f'{cls.__class__.__module__}.{cls.__class__.__name__}')

        # register the class
        if not isabstract(cls):
            cls._storage_class_registry.append(cls)

        # Ensure each class get's its own registry object:
        cls._storage_registry = {}
        cls._context_registry_backup = {}

    # TODO: the functions below and above should not be required anymore. The
    # top one, perhaps to set the logger

    # The factory below can also accept singleton objects of the following
    # class as input:
    class FactoryBehavior:
        pass

    # The following realization will return all registered objects.
    AllRegistered = FactoryBehavior()
    # Planned to be extended with AllAvailable

    # Type hint for a storage factory. Also must be runtime checkable to throw
    # an error when a factory is constructed that did not have a factory as
    # base_storage input. Otherwise, error throwing comes too late.
    @runtime_checkable
    class Factory(Protocol):
        ''' TypeDef for factory function to construct Storage objects '''
        @overload
        def __call__(self, name: str) -> Storage:
            ...

        @overload
        def __call__(self,
                     name: Storage.FactoryBehavior
                     ) -> list[Storage]:
            ...

        @abstractmethod
        def __call__(self,
                     name: str | Storage.FactoryBehavior
                     ) -> Storage | list[Storage]:
            ''' Factory to construct Storage objects '''

    # TODO: the interface is not very awesome. (1) The storage_get_fun would be
    # better to get removed. There is just a problem with getting the right
    # arguments to call the implementing storage classes get(). (2) The
    # base_storage argument is a bit of a special case but may be OK.
    @classmethod
    def get_factory(cls,
                    storage_get_fun: Callable[[str], Storage],
                    location: str | None = None,
                    base_storage: Storage.Factory | None = None,
                    ) -> Storage.Factory:
        ''' Return a factory for Storage objects

        The factory is a simplified constructor, returning a Storage object.
        You have to define any setting for your Storage, except name and meta.
        '''
        # throw an error if base_storage is proviced but is not a factory in
        # this context.
        if (
            (location is None and base_storage is None) or
            (location is not None and base_storage is not None)
        ):
            raise AppxfStorageError(
                'Storage.get_factory() needs either base_storage or '
                'location being defined.')
        if (
            base_storage is not None and
            not isinstance(base_storage, Storage.Factory)
        ):
            raise AppxfStorageError(
                'base_storage must be a storage factory '
                'in context of get_factory()')
        if base_storage is None:
            def factory(
                    name: str | Storage.FactoryBehavior
                    ) -> Storage | list[Storage]:
                if isinstance(name, Storage.FactoryBehavior):
                    if name is Storage.AllRegistered:
                        if location not in cls._storage_registry:
                            return []
                        return list(cls._storage_registry[location].values())
                return storage_get_fun(name)
        else:
            def factory(
                    name: str | Storage.FactoryBehavior
                    ) -> Storage | list[Storage]:
                if isinstance(name, Storage.FactoryBehavior):
                    if name is Storage.AllRegistered:
                        # without a base_storage object, we cannot know the
                        # location. But we can access the factory of the base
                        # storage with the same argument:
                        return [
                            storage for storage
                            in base_storage(Storage.AllRegistered)
                            if isinstance(storage, cls)]
                # derived storage must use base_storage but this is already
                # constructed as part of the calling get_storage_factory.
                return storage_get_fun(name)
                # TODO: now, in get factory - I cannot provide the "file"
                # argument to the actual constructor since it is just name in
                # the factory.
                #
                # Also: the derivation is screwed. super(cls, cls) would not
                # work if two derivatives redefine get().
        return factory

    def get_meta(self, meta: str) -> Storage:
        ''' Obtain meta storage from existing storage object

        If this is a storage derived from a base storage, the returned storage
        for meta files is of the base storage type.
        '''
        if self.base_storage is None:
            meta_storage = deepcopy(self)
        else:
            meta_storage = deepcopy(self.base_storage)
        meta_storage._meta = meta
        return meta_storage

    # #########################################################################
    # REGISTRY BEHAVIOR
    # /

    # The use case for get() is mainly testing or complex application
    # architectures. Testing may need to simulate two aplication instances
    # accessing the same shared storage - both instances creating a storage
    # object for it. A complex application may have two modules that access the
    # same storage and should hide their storage object creation.
    #
    # Due to the location argument likely be called differently in the derived
    # storage, get() must be overloaded.
    #
    # TODO: The "create" option to switch between creation and error if not
    #   existent was removed. Check if this really has no use case anymore.

    # @classmethod
    # @abstractmethod
    # def get(cls, **kwargs) -> Storage:
    #    ''' Get a known storage object or create one.
    #
    #    Use get_meta() to obetain meta data storable from an existing storage.
    #    '''
    #    cls._verify_constructor_arguments(argumnents=list(kwargs.keys()))
    #    # The below is a sample implementation:
    #    storage = cls.get_existing_storage(name=cls.get_name(**kwargs),
    #                                       location=cls.get_location(**kwargs))

    #    if storage is None:
    #        storage = cls(**kwargs)
    #    return storage

    @classmethod
    @abstractmethod
    def get(cls,
            name: str,
            location: str,
            storage_init_fun: Callable[..., Storage],
            user: str = '',
            ) -> Storage:
        ''' Get a known storage object or create one.

        Use get_meta() to obetain meta data storable from an existing storage.
        '''
        # try using existing storage
        storage = cls.get_existing_storage(name=name, location=location)
        if storage is not None:
            return storage
        # use class constructor, but strip the typical cls and __class__:
        return storage_init_fun()

    @classmethod
    def get_existing_storage(cls,
                             name: str,
                             location: str,
                             ) -> Storage | None:
        # block if context was used and not context is set (object creation
        # blocked for safety reasons):
        if Storage._context_locked:
            raise AppxfStorageError(
                'You locked object creation by switch_context("") '
                'after starting using the context feature. '
                'Either keep a valid context, or reconsider the usage of '
                'switch_context()')

        if cls.is_registered(name, location=location):
            return cls._storage_registry[location][name]
        return None

    @classmethod
    def switch_context(cls, context: str):
        ''' Switch context for storage registry

        Do not use in applications, unless you are certain on the impact.
        Context is a feature added mainly for TESTING use cases involving
        multiple aplication instances.
        '''
        # block context switching if current context is not set and there is
        # stuff in the registry:
        if not Storage._context:
            for this_cls in Storage._storage_class_registry:
                if this_cls._storage_registry:
                    raise AppxfStorageError(
                        f'Context switch not allowed if storage was already '
                        f'created without context. '
                        f'Storages registered for: {this_cls.__name__}')
        # handle context change in all storage classes
        for this_cls in Storage._storage_class_registry:
            # create a backup
            if Storage._context:
                this_cls._context_registry_backup[Storage._context] = (
                    this_cls._storage_registry)
            # load new context or replace registry for new context
            if context in this_cls._context_registry_backup:
                this_cls._storage_registry = (
                    this_cls._context_registry_backup[context])
            else:
                this_cls._storage_registry = {}
        # Apply context lock if switching from valid to invalid context:
        if Storage._context and not context:
            Storage._context_locked = True
        if context:
            Storage._context_locked = False
        # context switch succesful:
        Storage._context = context

    @classmethod
    def _register_storage(cls, name: str, location: str, instance: Storage):
        ''' Register a storage to the class register

        You should not need to use this function when deriving storages since
        Storage.__init__() already ensures registration. This also includes the
        registration to the base class if necessary.
        '''
        if location not in cls._storage_registry:
            cls._storage_registry[location] = {}
        cls._storage_registry[location][name] = instance

    @classmethod
    def _unregister_storage(cls, location: str, name: str):
        ''' Deregister current storage '''
        if location not in cls._storage_registry:
            return
        if name not in cls._storage_registry[location]:
            return
        del cls._storage_registry[location][name]
        # also purge location if it is empty:
        if not cls._storage_registry[location]:
            del cls._storage_registry[location]

    def register(self, override: Storage | None = None):
        ''' Register this instance to this classes registry

        This function should remain unused. It is already registered upon
        construction and unregsitering it, targeting a later re-register may
        cause further problems. Function was added for consistency.
        '''
        if (
            override is not None and
            self.is_registered(self._name, location=self._location) and
            not override
        ):
            raise AppxfStorageError(
                f'{self.id()} is already registered in '
                f'{self.__class__.__name__}')
        if override is None:
            self._register_storage(name=self._name,
                                   location=self._location,
                                   instance=self)
        else:
            self._register_storage(name=self._name,
                                   location=self._location,
                                   instance=override)

    def unregister(self):
        ''' Unregister this instance

        Usage is not recommended. This function is used in context of reset()
        which should only be required in context of unit testing to purge the
        class variables.
        '''
        self._unregister_storage(name=self._name, location=self._location)
        if self._base_storage is not None:
            # While calling the same function, this get's executed in the
            # context of the base storage class and, therfore, affects the
            # registration there.
            self._base_storage.unregister()

    @classmethod
    def reset(cls):
        ''' Reset registered storages

        Should not be required in an applications but may be required during
        testing.
        '''
        # reset() on Storage will reset all known Storage classes:
        if cls == Storage:
            for this_cls in cls._storage_class_registry:
                this_cls.reset()
            # also reset the context
            Storage._context_registry_backup = {}
            Storage._context_locked = False
            return
        while cls._storage_registry:
            loc = next(iter(cls._storage_registry))
            # end condition for the while below is loc being removed via
            # unregister()->_unregister_storage()
            while loc in cls._storage_registry:
                name = next(iter(cls._storage_registry[loc]))
                cls._storage_registry[loc][name].unregister()
            # Note: if unregister() is called in the context of deriving
            # storages via the base_storage argument to __init__(),
            # unregister() will be called on the derived class and traverse
            # down into the base storages accordingly.

    @classmethod
    def is_registered(cls, name: str, location: str = '') -> bool:
        ''' Check if name in group is registered to storage class '''
        if location in cls._storage_registry:
            if name in cls._storage_registry[location]:
                return True
        return False

    # #########################################################################
    # CORE OBJECT
    # Construction and Storage Behavior
    # /
    def __init__(self,
                 name: str,
                 location: str = '',
                 user: str = '',
                 base_storage: Storage | None = None
                 ):
        ''' Constructor for Storage objects

        Arguments:
            name -- name of the storage item

        Keyword Arguments:
            meta -- used to define meta information for a storage item
                (default: {''})
            location -- physical location of the storage. Location and name
                must uniquely identify the physical storage (like a file in the
                file system). Sticking with files as examples, location+name
                must be different if different files are accessed while they
                must be the same if the same file is accessed. This must apply
                likewise if the storage does not implement a file based
                storage. This property is relevant for a proper registry but
                mandatory for the synchronization behavior. (default: {''})
            user -- who is accessing the stroage. This property is only
                relevant for shared storage locations which may be accessed by
                multiple instances of your application. See the registry module
                and SecureSharedStorage.
            base_storage -- You may want to add behavior like encryption to an
                existing storage. This Storage class already handles
                initialization and registration with this base storage for
                derived classes.
        '''
        # Cannot construct if locked by context:
        if Storage._context_locked:
            raise AppxfStorageError(
                'You locked object creation by switch_context("") '
                'after starting using the context feature. '
                'Either keep a valid context, or reconsider the usage of '
                'switch_context()')
        # Cannot construct an already registered object:
        if (
            location in self._storage_registry and
            name in self._storage_registry[location]
        ):
            raise AppxfStorageError(
                f'{self.__class__.__name__} already knows '
                f'a storage {location}::{name}')

        # construction
        super().__init__()
        self._name = name
        self._meta = ''
        self._location = location
        self._user = user
        self._base_storage = base_storage
        self._context = Storage._context

        # register newly created storage
        self._register_storage(name, location, self)
        # register in base storage, if applicable:
        if base_storage is not None:
            base_storage._register_storage(name, location, self)

    @property
    def name(self):
        ''' Name of the storage item.

        Within a storage class, group and name uniquely identify a storage
        item.
        '''
        return self._name

    @property
    def meta(self):
        ''' Identify storage as meta data '''
        return self._meta

    @property
    def location(self):
        ''' Physical location of the storage item

        Storage item and location uniquely identify the storage.
        '''
        return self._location

    @property
    def user(self):
        ''' User who is accessing the storage

        In case a storage location can be accessed by multiple application
        instances, the instance would typically identify itself by the logged
        in user.
        '''
        return self._user

    @property
    def base_storage(self) -> Storage | None:
        ''' Access base storage
        '''
        return self._base_storage

    def id(self) -> str:
        ''' ID for the storage object.

        Identify the storage object by class, location and name. In case of
        derived storage classes, the identity of the base storage is included.
        Same applies to storages that consider a current user accessing the
        data.
        '''
        # Examples:
        # LocalStorage(./path/to/file): file
        # SecurePrivate() on LocalStorage(./path/to/file): file
        # FtpStorate(www.something.de/ftp/path/to/file): file
        # SecureSharedStorage(user)
        #     on FtpStorage(www.something.de/ftp/path/to/file): file
        # FancyFiveTimesDerivesStorage(user)
        #     on StillOnlyRawStorage(location): file
        #
        # The following would be possible but questionable
        # FancyDerivedStorage(user) on
        #     FancyRawWithUser(user, URL/path/to/file): file
        #
        # Conclusion: derived storages can rely on the id() of the root storage
        base_storage_str = ''
        if self._base_storage is not None:
            base_storage_str = self._base_storage.id()

        context_str = f' (Context: {self._context})' if self._context else ''

        if self._user and base_storage_str:
            return (f'{self.__class__.__name__}'
                    f'({self._user}) on {base_storage_str}{context_str}')
        if base_storage_str:
            return (f'{self.__class__.__name__}'
                    f' on {base_storage_str}{context_str}')
        if self._user:
            return (f'{self.__class__.__name__}'
                    f'({self._user}, {self._location}): '
                    f'{self._name}{context_str}')
        # no user, no base storage
        return (f'{self.__class__.__name__}'
                f'({self._location}): '
                f'{self._name}{context_str}')

    # #########################################################################
    # CORE STORAGE
    # /

    def load(self) -> object:
        ''' Load data

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''
        return self.convert_from_raw(self.load_raw())

    def store(self, data: object):
        ''' Store data

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''
        # TODO: the hash or file content should be analyzed before generating a
        # new UUID - this may make this detail to a function that should be
        # executed on raw data?
        if not self._meta:
            self.set_meta_data(meta=MetaData(valid=True))
        self.store_raw(self.convert_to_raw(data=data))

    def convert_to_raw(self, data: object) -> object:
        ''' Converting object to raw storage data type

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''
        return data

    def convert_from_raw(self, data: object) -> object:
        ''' Converting object to raw storage data type

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''
        return data

    @abstractmethod
    def exists(self) -> bool:
        ''' Check existance in storage before loading '''

    @abstractmethod
    def store_raw(self, data: object):
        ''' Store interface to the actual storage

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''

    @abstractmethod
    def load_raw(self) -> object:
        ''' Load interface to the actual storage

        To decide what goes where, consider the following intended usage:
         1) store()/load() are the user interface. They take/provide original
            python data types and could handle extra tasks on the original
            python objects. They have a default implementation calling (2) and
            (3) while adding meta data required for synchronization. You should
            rely on these functions when implementing a new storage.
         2) _convert_to_raw()/_convert_from_raw() is responsible to convert, if
            required, the general python objects into the data type that can be
            handled by the underlying storage (like bytestreams for files). The
            default implementation applies no transformations.
         3) _store()/_load() cover the interface to the actual storage. There
            is no default implementation.
        '''

    # METADATA behavior
    #
    # Default behavior considers self._meta_data_enabled which could be
    # overwritten per object and uses storage names as name.meta to get/set
    # metadata. Both functions may be overwritten.

    # TODO: meta data is only reuquired in context of sync and there is no
    # option to deactivate it. The most negative concern is unneccesary disk
    # usage - general efficiency is not considered a major concern.

    # TODO: The concept does not include an extention of MetaData to hashes or
    # other content-specific information that may assist in synchroniziation.

    # TODO: there is no way yet to properly serialize to JSON. Currently, we
    # gat the JSON serialized bytestream from MetaData but LocalStorage would
    # apply whatever serializer was set to it. Defaulting an get_meta() to a
    # JSON serializer does not sound consistent. From StorageToBytes, allowing
    # to set the serializer on an existing meta storage is another idea but
    # does not sound appropriate either. The boundaries may be:
    #   * For normal storage, the serializer must be set upon construction.
    #     While, for SecureStorage not much else than CompactSerializer would
    #     be required.
    #   * For meta storage, the storable (if applicable) should decide how it
    #     is stored on the storage system. But this would also imply that the
    #     storable is aware of being stored into a StorageToBytes
    #   * Reformulation from above: StorageToBytes needs a way to
    #     define/overwrite the serialization for meta data types. >> This could
    #     be done wherever the meta data is introduced like:
    #     StorageToBytes.setMetaSerializer('meta', JsonSerializer)
    # The above is perfectly reasonable!

    def get_meta_data(self) -> MetaData | None:
        ''' Get meta data of stored data.

        Contains UUID and/or timestamp used for synchronization.
        '''
        meta_storage = self.get_meta('meta')
        if not meta_storage.exists():
            return None
        meta_state = self.get_meta('meta').load()
        return MetaData(state=meta_state)

    def set_meta_data(self, meta: MetaData):
        ''' Set updated meta data

        Contains UUID and/or timestamp used for synchronization.
        '''
        meta_storage = self.get_meta('meta')
        meta_storage.store(meta.get_state())
    # TODO: this set/get _meta_data is a name clash to the "meta" arguments to
    # store/load.
