import sublime
import sublime_plugin
import os
import sys

PLUGIN_DIR = os.path.dirname(__file__)
JEDI_LIB_PATH = os.path.join(PLUGIN_DIR, "jedi_lib")
if JEDI_LIB_PATH not in sys.path:
    sys.path.append(JEDI_LIB_PATH)

import jedi

class JediSyntaxErrorHighlighter(sublime_plugin.EventListener):
    def __init__(self):
        super().__init__()
        self.error_messages = {}  # Store error messages with regions as keys

    def on_modified_async(self, view):
    # def on_post_save_async(self, view):
        if not view.match_selector(0, "source.python"):
            return

        file_content = view.substr(sublime.Region(0, view.size()))
        file_path = view.file_name()

        # Clear existing highlights and status
        view.erase_regions("jedi_syntax_errors")
        view.erase_status("jedi_syntax_error")

        self.error_messages = {}

        try:
            script = jedi.Script(code=file_content, path=file_path, environment=jedi.get_system_environment("3"))
            syntax_errors = script.get_syntax_errors()

            error_regions = []
            messages = []
            for error in syntax_errors:
                error_line = error.line
                error_column = error.column
                error_message = error.get_message()

                # Create a region for the invalid code
                # error_region = sublime.Region(
                #     view.text_point(error_line - 1, max(error_column - 1, 0)),
                #     view.text_point(error_line - 1,  max(error_column, 0))
                # )
                error_start = view.text_point(error_line - 1, 0)  # Start of the line
                error_end = view.line(error_start).end()
                error_region = sublime.Region(error_start, error_end)

                # Store the error message for later use
                self.error_messages[str(error_region)] = error_message

                # Highlight the error
                error_region = view.line(view.text_point(error_line - 1, 0))
                error_regions.append(error_region)
                messages.append(f"Line {error_line}: {error_message}")

            if error_regions:
                # Add highlight
                view.add_regions(
                    "jedi_syntax_errors",
                    error_regions,
                    scope="invalid",
                    icon="dot",
                    flags=sublime.DRAW_NO_FILL
                )

                # Show the first error in the status bar
                view.set_status("jedi_syntax_error", messages[0])

            # Log all errors to the console
            for message in messages:
                print(message)

        except Exception as ex:
            print(f"Error in Jedi analysis: {ex}")

    def on_hover(self, view, point, hover_zone):
        """
        Show the error reason when hovering over the underlined region.
        """
        if hover_zone != sublime.HOVER_TEXT:
            return

        # Check if the hover point is within any error region
        for region_key, error_message in self.error_messages.items():
            error_region = sublime.Region(*map(int, region_key.strip("Region()").split(", ")))
            if error_region.contains(point):
                # Show the error message as a popup
                view.show_popup(
                    content=error_message,
                    location=point,
                    flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                    max_width=600
                )
                break