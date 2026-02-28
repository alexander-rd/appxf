# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
from tkinter import filedialog, messagebox

from appxf.gui.locale import _
from appxf.gui.registration_user import log
from appxf.registry import (
    AppxfRegistryRoleError,
    AppxfRegistryUnknownUserError,
    Registry,
)


def handle_manual_config_update_load(
    parent,
    registry: Registry,
    initial_path: str,
    initial_file: str = "config.update",
):
    """File dialog for loading a manual config update file

    Keyword arguments:
        parent -- Parent tkinter window
        registry -- Registry object for config update interface
        initial_path -- Initial path for file dialog
        initial_file -- Initial file name for file dialog
    """
    file_path = filedialog.askopenfilename(
        parent=parent,
        title=_("dialog", "Config Update File"),
        initialdir=initial_path,
        initialfile=initial_file,
        defaultextension="",
    )
    if not file_path:
        return

    try:
        with open(file_path, "rb") as fh:
            update_bytes = fh.read()
        registry.set_manual_config_update_bytes(update_bytes)
    except OSError as e:
        log.error("Failed to read response file: %s", e)
        messagebox.showerror(
            "Error",
            _("error", "Failed to read file: {}").format(e),
            parent=parent,
        )
    except (AppxfRegistryUnknownUserError, AppxfRegistryRoleError) as e:
        log.error("Failed to update: %s", e)
        messagebox.showerror(
            "Error",
            _("error", "Failed to apply config update: {}").format(e),
            parent=parent,
        )


def handle_manual_config_update_write(
    parent,
    registry: Registry,
    initial_path: str,
    initial_file: str = "config.update",
    sections: list[str] | None = None,
    include_user_db: bool = True,
):
    """File dialog for writing a manual config update file.

    Keyword arguments:
        parent -- Parent tkinter window
        registry -- Registry object for config update interface
        initial_path -- Initial path for file dialog
        initial_file -- Initial file name for file dialog
        sections -- List of sections to include in the update. If None, all
            sections except 'USER' are included.
        include_user_db -- Whether to include the user database in the update
            {default: True}
    """
    if sections is None:
        sections = registry._config.sections
        if "USER" in sections:
            sections.remove("USER")

    file_path = filedialog.asksaveasfilename(
        parent=parent,
        title=_("dialog", "Config Update File"),
        initialdir=initial_path,
        initialfile=initial_file,
        defaultextension="",
    )
    if not file_path:
        return

    try:
        update_bytes = registry.get_manual_config_update_bytes(
            sections=sections, include_user_db=include_user_db
        )
        with open(file_path, "wb") as fh:
            fh.write(update_bytes)

    except OSError as e:
        log.error("Failed to write config update file: %s", e)
        messagebox.showerror(
            "Error",
            _("error", "Failed to write file: {}").format(e),
            parent=parent,
        )
    # we do NOT handle wrong role exception here since the this option should
    # only be called if user is admin
