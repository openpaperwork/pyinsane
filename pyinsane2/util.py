import logging


logger = logging.getLogger(__name__)


__all__ = [
    'AliasOption',
    'PyinsaneException',
]


class PyinsaneException(Exception):
    def __init__(self, status):
        Exception.__init__(self, str(status))
        self.status = status


class AliasOption(object):
    def __init__(self, name, alias_for, options):
        self.__dict__['alias_for'] = alias_for
        self.__dict__['_options'] = [
            options[opt_name] for opt_name in alias_for
        ]
        self.__dict__['name'] = name

    def __getattr__(self, attr):
        if '_options' not in self.__dict__:
            raise AttributeError()
        return getattr(self.__dict__['_options'][0], attr)

    def __setattr__(self, attr, new_value):
        last_exc = None
        for opt in self.__dict__['_options']:
            try:
                setattr(opt, attr, new_value)
            except Exception as exc:
                # keep trying to set the options for consistency
                # (some driver may return an error while accepting the value
                # ...)
                logger.exception("Failed to set option {}: {}".format(
                    self.__dict__['name'], exc
                ))
                last_exc = exc
        if last_exc:
            raise last_exc

    def __str__(self):
        return ("Option [{}] (alias for {})".format(
            self.__dict__['name'], self.__dict__['alias_for']
        ))
