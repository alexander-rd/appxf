# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from appxf import logging
from appxf.setting import SettingDict

log = logging.get_logger(__name__)

config_property_template = SettingDict(
    {"server": (str,), "port": (str,), "user": (str,), "password": ("password",)}
)
# TODO: Properties could add "URL"


class Email(MIMEMultipart):
    """Email Object

    If you plan to send multiple Emails, it is recommended to collect them
    first in a list and then use sendmail.send() for this list. In this way,
    you only need to connect to the SMTP server once, processing all Emails at
    once.
    """

    def __init__(self, message="", file_list=[], **kwargs):
        """Email Object

        This class is wrapping MIMEMultipart while you can construct it
        directly like: `email = Email(Subject='Email Title', message='Text',
        To='to-email@address.org')`
        """
        # input handling
        super().__init__()
        # TODO: the above is not correct, it should pass **kwargs in case of
        # multiple inheritance. But sendmail has no test coverage and risk of
        # regressions was too high.

        for key, value in kwargs.items():
            if key in ["To", "CC", "BCC"]:
                if isinstance(value, list):
                    value = ", ".join(value)
                self[key] = value
                continue
            if key in ["Subject", "From"]:
                self[key] = value
                continue
            log.warning(f'Parameter "{key}" is not supported (value: {value})')
        for key in ["To", "CC", "BCC", "Subject", "From"]:
            if key not in kwargs:
                self[key] = ""

        self.attach(MIMEText(message))

        for f in file_list:
            with open(f, "rb") as file:
                part = MIMEApplication(file.read(), Name=os.path.basename(f))
            # After the file is closed
            part["Content-Disposition"] = (
                f'attachment; filename="{os.path.basename(f)}"'
            )
            self.attach(part)

        log.debug(
            f"Subject: {self['Subject']}, "
            f"To: {self['To']}, "
            f"CC: {self['CC']}, "
            f"BCC: {self['BCC']}, "
            f"files: {file_list}"
        )

    def send(self, config: dict):
        # Forward to module level send function
        send(self, config)


def send(
    email: list[Email] | Email,
    config: dict | SettingDict,
    debug_send_email: bool = True,
    debug_substituttion_email: str = "",
):

    if isinstance(email, MIMEMultipart):
        email = [email]

    with smtplib.SMTP(config["server"], config["port"]) as server:
        if debug_send_email:
            # identify ourselves to smtp gmail client
            server.ehlo()
            # secure our email with tls encryption
            server.starttls()
            # re-identify ourselves as an encrypted connection
            server.ehlo()
            server.login(config["user"], config["password"])

        for this_msg in email:
            to = this_msg["To"].split(", ")
            cc = this_msg["CC"].split(", ")
            bcc = this_msg["BCC"].split(", ")

            log.debug(
                f"subject: {this_msg['Subject']}, "
                f"To: {' '.join(to)}, "
                f"CC: {' '.join(cc)}, "
                f"BCC: {' '.join(bcc)}"
            )

            target_list = (
                [a for a in to if a] + [a for a in cc if a] + [a for a in bcc if a]
            )
            target = set(target_list)
            if debug_substituttion_email:
                log.debug(
                    f"Using substitution Email: "
                    f"{debug_substituttion_email} "
                    f"instead of {target}"
                )
                target = [debug_substituttion_email]
            else:
                log.debug(f"Sending to: {target}")

            if debug_send_email:
                senderr = server.sendmail(
                    this_msg["From"], list(target), this_msg.as_string()
                )
                if senderr:
                    log.debug("Emails sending with error:")
                    log.debug(str(senderr))
                else:
                    log.debug("Emails sent succesfully")
            else:
                log.debug("NOT sending Emails (debug_send_email)")

        if debug_send_email:
            server.quit()
