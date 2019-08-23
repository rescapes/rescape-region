from promise import is_thenable
from rescape_region.schema_models.schema import dump_errors

class DebugMiddleware(object):
    def on_error(self, error):
        dump_errors(dict(errors=[error]))

    def resolve(self, next, root, info, **args):
        result = next(root, info, **args)
        if is_thenable(result):
            result.catch(self.on_error)

        return result