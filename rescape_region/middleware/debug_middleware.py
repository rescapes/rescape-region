from promise import is_thenable
from rescape_python_helpers import ramda as R

from rescape_region.schema_models.schema import dump_errors, log_request_body


class DebugMiddleware(object):
    def on_error(self, error, info):
        log_request_body(info, error)
        dump_errors(dict(errors=[error]))

    def resolve(self, next, root, info, **args):
        result = next(root, info, **args)
        if is_thenable(result):
            result.catch(self.on_error)
            # Top level only
            if R.length(info.path) == 1:
                result.then(lambda response: log_request_body(info, response))

        return result

