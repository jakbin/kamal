import os
import sys
import sublime
import sublime_plugin

try:
    import jedi
except ImportError:
    PLUGIN_DIR = os.path.dirname(__file__)
    JEDI_LIB_PATH = os.path.join(PLUGIN_DIR, "jedi_lib")
    if JEDI_LIB_PATH not in sys.path:
        sys.path.append(JEDI_LIB_PATH)
    import jedi


ENVIRONMENT = jedi.get_system_environment("3")

class JediAutocompleteListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # Ensure the current file is a Python file
        if not view.match_selector(locations[0], "source.python"):
            return []

        # Get the current file's content and cursor position
        file_content = view.substr(sublime.Region(0, view.size()))

        script = jedi.Script(
            code=file_content, path=view.file_name(), environment=ENVIRONMENT
        )

        # Fetch completions
        completions = script.complete()
        # Format completions for Sublime Text
        suggestions = [
            (
                "{}\t{}".format(comp.name, comp.type),
                comp.name
            )
            for comp in completions
        ]

        return suggestions