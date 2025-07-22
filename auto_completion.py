import os
import sys

import jedi.api
import jedi.api.environment
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

try:
    ENVIRONMENT = jedi.get_system_environment("3")
except jedi.api.environment.InvalidPythonEnvironment:
    ENVIRONMENT = jedi.get_default_environment()

class JediAutocompleteListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.python"):
            return []

        try:

            file_content = view.substr(sublime.Region(0, view.size()))
            
            # Get the cursor position (line and column)
            cursor_pos = locations[0]
            line, column = view.rowcol(cursor_pos)
            
            # Jedi uses 1-based line numbering
            line += 1

            script = jedi.Script(
                code=file_content, 
                path=view.file_name(), 
                environment=ENVIRONMENT
            )

            # Get completions at the specific cursor position
            completions = script.complete(line=line, column=column)
            
            suggestions = []
            for comp in completions:
                # Create more informative completion entries
                trigger = comp.name
                contents = comp.name
                
                # Add type information to the trigger for better display
                if comp.type:
                    trigger = f"{comp.name}\t{comp.type}"
                
                suggestions.append((trigger, contents))

            return suggestions

        except Exception as e:
            print(f"Jedi completion error: {e}")
            return []

    def on_hover(self, view, point, hover_zone):
        """
        Show documentation on hover with syntax highlighting
        """
        if not view.match_selector(point, "source.python"):
            return
            
        if hover_zone != sublime.HOVER_TEXT:
            return
            
        try:
            word_region = view.word(point)
            row, col = view.rowcol(point)
            
            script = jedi.Script(
                code=view.substr(sublime.Region(0, view.size())),
                path=view.file_name()
            )
            
            definitions = script.help(row + 1, col) or script.get_signatures(row + 1, col)
            
            if definitions:
                def_info = definitions[0]
                doc = def_info.docstring()
                if doc:
                    styles = """
                        <style>
                            body { 
                                font-family: "Consolas", monospace; 
                                font-size: 1.0em;
                                padding: 5px;
                            }
                            .signature { 
                                color: #89DDFF; 
                                margin-bottom: 10px;
                            }
                            .example {
                                color: #89DDFF;
                                margin: 10px 0;
                            }
                            .keyword { color: #F07178; }
                            .param { color: #A9DC76; }
                            .param-default { color: #FFB86C; }
                            .type { color: #78DCE8; }
                            .string { color: #C3E88D; }
                            .desc { 
                                color: #CCCCCC;
                                margin-top: 10px;
                                line-height: 1.4;
                            }
                            .section { 
                                color: #F07178;
                                font-weight: bold;
                                margin-top: 10px;
                            }
                        </style>
                    """
                    
                    # Split the docstring into parts
                    parts = doc.split("\n\n")
                    signature = parts[0]
                    example = parts[1] if len(parts) > 1 else ""
                    description = parts[2] if len(parts) > 2 else ""
                    
                    # Format the signature
                    signature = signature.replace(" -> ", " <span class='keyword'>-></span> ")
                    signature = signature.replace("Optional[", "<span class='type'>Optional[</span>")
                    signature = signature.replace("]", "<span class='type'>]</span>")
                    signature = signature.replace("None", "<span class='type'>None</span>")
                    signature = signature.replace("bool", "<span class='type'>bool</span>")
                    signature = signature.replace("str", "<span class='type'>str</span>")
                    signature = signature.replace("object", "<span class='type'>object</span>")
                    
                    # Add line breaks to signature
                    signature = signature.replace(", ", ",<br>    ")
                    
                    # Format parameters
                    import re
                    signature = re.sub(r'(\w+):', r'<span class="param">\1</span>:', signature)
                    signature = re.sub(r'=\.\.\.', r'=<span class="param-default">...</span>', signature)
                    
                    # Format the example
                    example = example.replace("print", "<span class='keyword'>print</span>")
                    example = example.replace("value", "<span class='param'>value</span>")
                    example = example.replace("sys.stdout", "<span class='param'>sys.stdout</span>")
                    example = example.replace("' '", "<span class='string'>' '</span>")
                    example = example.replace("'\\n'", "<span class='string'>'\\n'</span>")
                    example = example.replace("False", "<span class='keyword'>False</span>")
                    example = example.replace("sep=", "<span class='param'>sep=</span>")
                    example = example.replace("end=", "<span class='param'>end=</span>")
                    example = example.replace("file=", "<span class='param'>file=</span>")
                    example = example.replace("flush=", "<span class='param'>flush=</span>")
                    
                    # Format the description
                    description = description.replace("\n", "<br>")
                    description = re.sub(
                        r'Optional keyword arguments:',
                        r'<span class="section">Optional keyword arguments:</span>',
                        description
                    )
                    
                    # Build the final HTML content
                    content = f"""
                        {styles}
                        <div class='signature'>{signature}</div>
                        <div class='example'>{example}</div>
                        <div class='desc'>{description}</div>
                    """
                    
                    view.show_popup(
                        content,
                        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY | sublime.COOPERATE_WITH_AUTO_COMPLETE,
                        location=point,
                        max_width=800
                    )
                    
        except Exception as e:
            print(f"Jedi hover error: {str(e)}")