import sublime
import sublime_plugin
import ast
import builtins
import os
import sys

class UndefinedVariableChecker(ast.NodeVisitor):
    def __init__(self):
        self.defined_vars = set(dir(builtins))  # Include built-in names
        self.undefined_vars = set()
        self.scope_vars = [set()]  # Stack for handling different scopes
        self.imports = set()
        self.from_imports = {}
        self.defined_functions = set()
        self.defined_classes = set()
        self.assigned_vars = set()
        self.exception_vars = set()
        self.comprehension_vars = set()  # Track comprehension variables

        # Add all special Python variables
        self.special_vars = {
            '__name__',
            '__file__',
            '__doc__',
            '__package__',
            '__cached__',
            '__spec__',
            '__annotations__',
            '__builtins__',
            '__loader__',
            '__path__',
            '__dict__',
            '__module__',
            '__class__',
            '__bases__',
            '__mro__',
            '__subclasses__',
            '__init__',
            '__new__',
            '__del__',
            '__repr__',
            '__str__',
            '__format__',
            '__len__',
            '__getitem__',
            '__setitem__',
            '__delitem__',
            '__iter__',
            '__next__',
            '__contains__',
            '__call__',
            '__enter__',
            '__exit__',
            '__get__',
            '__set__',
            '__delete__',
            '__slots__',
            '__metaclass__',
            '__qualname__',
            '__all__',
            'self',
            'cls',
        }
        self.defined_vars.update(self.special_vars)

    def is_special_var(self, var_name):
        """Check if a variable name is a special Python variable"""
        # Check if it's in our predefined special vars
        if var_name in self.special_vars:
            return True
            
        # Check if it follows dunder pattern (__x__)
        if (len(var_name) > 4 and 
            var_name.startswith('__') and 
            var_name.endswith('__')):
            return True
            
        return False

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.scope_vars[-1].add(node.id)
            self.assigned_vars.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            # First check if it's a special variable
            if self.is_special_var(node.id):
                return

            is_defined = (
                any(node.id in scope for scope in self.scope_vars) or
                node.id in self.defined_vars or
                node.id in self.imports or
                node.id in self.defined_functions or
                node.id in self.defined_classes or
                node.id in self.assigned_vars or
                node.id in self.from_imports or
                node.id in self.exception_vars or
                node.id in self.comprehension_vars  # Check comprehension variables
            )
            if not is_defined:
                # Don't add to undefined if it's a comprehension variable
                if not self._is_in_comprehension(node):
                    self.undefined_vars.add((node.id, node.lineno))

    def _is_in_comprehension(self, node):
        """Check if a Name node is being used in a comprehension target"""
        # Walk up the AST to find parent nodes
        for parent in ast.walk(self.current_tree):
            for child in ast.iter_child_nodes(parent):
                if child == node:
                    # Check if parent is a comprehension
                    if isinstance(parent, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                        return True
                    # Check if parent is a comprehension generator
                    if isinstance(parent, ast.comprehension):
                        if parent.target == node:
                            return True
        return False

    def visit_ListComp(self, node):
        # Create a new scope for the list comprehension
        old_comprehension_vars = self.comprehension_vars.copy()
        
        # Add the loop variables from all generators to comprehension vars
        for gen in node.generators:
            if isinstance(gen.target, ast.Name):
                self.comprehension_vars.add(gen.target.id)
            elif isinstance(gen.target, ast.Tuple):
                for elt in gen.target.elts:
                    if isinstance(elt, ast.Name):
                        self.comprehension_vars.add(elt.id)
                        
        # Visit the comprehension components
        self.generic_visit(node)
        
        # Restore the previous comprehension vars
        self.comprehension_vars = old_comprehension_vars

    # Also handle other types of comprehensions similarly
    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_For(self, node):
        # This method defines the loop variable before visiting its children
        if isinstance(node.target, ast.Name):
            self.scope_vars[-1].add(node.target.id)
        elif isinstance(node.target, ast.Tuple):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.scope_vars[-1].add(elt.id)
        # Visit the loop body and other parts
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name:  # This is the 'e' in 'except Exception as e'
            self.exception_vars.add(node.name)
            self.scope_vars[-1].add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Add class name to defined variables
        self.defined_classes.add(node.name)
        self.scope_vars[-1].add(node.name)
        
        # New scope for class
        self.scope_vars.append(set())
        self.generic_visit(node)
        self.scope_vars.pop()

    def visit_FunctionDef(self, node):
        # Add function name to defined variables
        self.defined_functions.add(node.name)
        self.scope_vars[-1].add(node.name)
        
        # Create new scope for function arguments and body
        function_scope = set()
        
        # Add arguments to the new scope
        for arg in node.args.args:
            function_scope.add(arg.arg)
            
        # Handle varargs and kwargs
        if node.args.kwarg:
            function_scope.add(node.args.kwarg.arg)
        if node.args.vararg:
            function_scope.add(node.args.vararg.arg)
            
        self.scope_vars.append(function_scope)
        self.generic_visit(node)
        self.scope_vars.pop()

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname:
                self.imports.add(alias.asname)
            else:
                self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ''
        for alias in node.names:
            if alias.asname:
                self.from_imports[alias.asname] = f"{module}.{alias.name}"
                self.imports.add(alias.asname)
            else:
                self.from_imports[alias.name] = f"{module}.{alias.name}"
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_Module(self, node):
        self.current_tree = node
        self.generic_visit(node)

class CheckUndefinedVariablesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        check_undefined_variables(self.view)

class UndefinedVariablesEventListener(sublime_plugin.EventListener):
    def on_post_save(self, view):
        # Only check Python files
        if view.file_name() and view.file_name().endswith('.py'):
            check_undefined_variables(view)

def check_undefined_variables(view):
    # Get the entire file content
    region = sublime.Region(0, view.size())
    content = view.substr(region)
    
    try:
        # Parse the code
        tree = ast.parse(content)
        checker = UndefinedVariableChecker()
        checker.visit(tree)
        
        # Clear existing highlights
        view.erase_regions('undefined_vars')
        
        # Highlight undefined variables
        if checker.undefined_vars:
            regions = []
            for var_name, line_no in checker.undefined_vars:
                # Get the line region
                line_region = view.line(view.text_point(line_no - 1, 0))
                line_text = view.substr(line_region)
                
                # Find all occurrences of the variable in the line
                start = 0
                while True:
                    idx = line_text.find(var_name, start)
                    if idx == -1:
                        break
                    # Make sure we found a whole word
                    if (idx == 0 or not line_text[idx-1].isalnum()) and \
                       (idx + len(var_name) == len(line_text) or \
                        not line_text[idx + len(var_name)].isalnum()):
                        regions.append(sublime.Region(
                            line_region.begin() + idx,
                            line_region.begin() + idx + len(var_name)
                        ))
                    start = idx + 1
            
            # Add squiggly underlines to undefined variables
            view.add_regions(
                'undefined_vars',
                regions,
                'invalid',
                'dot',
                sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SQUIGGLY_UNDERLINE
            )
            
            # Show error message
            undefined_vars_list = sorted(set(var_name for var_name, _ in checker.undefined_vars))
            message = "Undefined variables found: " + ", ".join(undefined_vars_list)
            sublime.status_message(message)
        else:
            sublime.status_message("No undefined variables found")
            
    except SyntaxError as e:
        sublime.error_message(f"Syntax error in the code: {str(e)}")
    except Exception as e:
        sublime.error_message(f"Error checking variables: {str(e)}")