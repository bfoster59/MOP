#!/usr/bin/env python3
"""
Code Structure and Quality Analysis for MOP Gear Metrology System
Analyzes modularity, complexity, and architectural patterns
"""

import ast
import os
import sys
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FunctionAnalysis:
    name: str
    line_count: int
    complexity: int
    parameters: int
    docstring: bool
    return_annotation: bool

@dataclass
class ClassAnalysis:
    name: str
    methods: int
    line_count: int
    inheritance: List[str]
    docstring: bool

@dataclass
class FileAnalysis:
    filename: str
    line_count: int
    functions: List[FunctionAnalysis]
    classes: List[ClassAnalysis]
    imports: List[str]
    complexity_score: int
    maintainability_index: float

class CodeAnalyzer:
    """Comprehensive code structure analyzer"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.file_analyses: List[FileAnalysis] = []
        
    def analyze_file(self, filepath: str) -> FileAnalysis:
        """Analyze a single Python file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
            return None
            
        # Count lines
        line_count = len(content.splitlines())
        
        # Analyze functions
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_analysis = self._analyze_function(node, content)
                functions.append(func_analysis)
            elif isinstance(node, ast.ClassDef):
                class_analysis = self._analyze_class(node, content)
                classes.append(class_analysis)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_imports(node))
        
        # Calculate complexity metrics
        complexity_score = self._calculate_complexity(tree)
        maintainability_index = self._calculate_maintainability(
            line_count, complexity_score, len(functions) + len(classes)
        )
        
        return FileAnalysis(
            filename=os.path.basename(filepath),
            line_count=line_count,
            functions=functions,
            classes=classes,
            imports=imports,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index
        )
    
    def _analyze_function(self, node: ast.FunctionDef, content: str) -> FunctionAnalysis:
        """Analyze a function definition"""
        # Count lines in function
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        line_count = end_line - start_line + 1
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_function_complexity(node)
        
        # Count parameters
        parameters = len(node.args.args)
        
        # Check for docstring
        docstring = (isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, (ast.Str, ast.Constant))) if node.body else False
        
        # Check for return annotation
        return_annotation = node.returns is not None
        
        return FunctionAnalysis(
            name=node.name,
            line_count=line_count,
            complexity=complexity,
            parameters=parameters,
            docstring=docstring,
            return_annotation=return_annotation
        )
    
    def _analyze_class(self, node: ast.ClassDef, content: str) -> ClassAnalysis:
        """Analyze a class definition"""
        # Count methods
        methods = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        
        # Count lines
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        line_count = end_line - start_line + 1
        
        # Extract inheritance
        inheritance = [base.id for base in node.bases if isinstance(base, ast.Name)]
        
        # Check for docstring
        docstring = (isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, (ast.Str, ast.Constant))) if node.body else False
        
        return ClassAnalysis(
            name=node.name,
            methods=methods,
            line_count=line_count,
            inheritance=inheritance,
            docstring=docstring
        )
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate overall file complexity"""
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                               ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_maintainability(self, lines: int, complexity: int, components: int) -> float:
        """Calculate maintainability index (simplified version)"""
        # Simplified MI = 171 - 5.2*log(HV) - 0.23*CC - 16.2*log(LOC)
        # Where HV=Halstead Volume, CC=Cyclomatic Complexity, LOC=Lines of Code
        
        import math
        
        # Simplified calculation (without full Halstead metrics)
        log_lines = math.log(max(lines, 1))
        log_complexity = math.log(max(complexity, 1))
        
        mi = 100 - (log_lines * 10) - (complexity * 0.5) - (components * 2)
        return max(0, min(100, mi))  # Clamp between 0-100
    
    def _extract_imports(self, node) -> List[str]:
        """Extract import names from import statements"""
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
        
        return imports
    
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all Python files in the project"""
        python_files = []
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    python_files.append(filepath)
        
        for filepath in python_files:
            analysis = self.analyze_file(filepath)
            if analysis:
                self.file_analyses.append(analysis)
        
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_lines = sum(f.line_count for f in self.file_analyses)
        total_functions = sum(len(f.functions) for f in self.file_analyses)
        total_classes = sum(len(f.classes) for f in self.file_analyses)
        
        # Complexity statistics
        complexities = [f.complexity_score for f in self.file_analyses]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        
        # Maintainability statistics
        maintainabilities = [f.maintainability_index for f in self.file_analyses]
        avg_maintainability = sum(maintainabilities) / len(maintainabilities) if maintainabilities else 0
        
        # Find problematic functions (high complexity)
        problem_functions = []
        for file_analysis in self.file_analyses:
            for func in file_analysis.functions:
                if func.complexity > 10 or func.line_count > 50:
                    problem_functions.append((file_analysis.filename, func))
        
        # Find large classes
        large_classes = []
        for file_analysis in self.file_analyses:
            for cls in file_analysis.classes:
                if cls.line_count > 200 or cls.methods > 20:
                    large_classes.append((file_analysis.filename, cls))
        
        return {
            'total_files': len(self.file_analyses),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'average_complexity': avg_complexity,
            'average_maintainability': avg_maintainability,
            'problem_functions': problem_functions,
            'large_classes': large_classes,
            'file_analyses': self.file_analyses
        }
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        summary = self.analyze_all_files()
        
        print("="*80)
        print("CODE STRUCTURE AND QUALITY ANALYSIS REPORT")
        print("="*80)
        
        print(f"Total files analyzed: {summary['total_files']}")
        print(f"Total lines of code: {summary['total_lines']:,}")
        print(f"Total functions: {summary['total_functions']}")
        print(f"Total classes: {summary['total_classes']}")
        print(f"Average complexity: {summary['average_complexity']:.1f}")
        print(f"Average maintainability: {summary['average_maintainability']:.1f}")
        
        # File-by-file analysis
        print("\n" + "-"*60)
        print("FILE ANALYSIS")
        print("-"*60)
        
        for analysis in sorted(self.file_analyses, key=lambda x: x.line_count, reverse=True):
            print(f"\n{analysis.filename} ({analysis.line_count} lines)")
            print(f"  Functions: {len(analysis.functions)}")
            print(f"  Classes: {len(analysis.classes)}")
            print(f"  Complexity: {analysis.complexity_score}")
            print(f"  Maintainability: {analysis.maintainability_index:.1f}")
            print(f"  Imports: {len(analysis.imports)}")
        
        # Problem functions
        if summary['problem_functions']:
            print("\n" + "-"*60)
            print("HIGH COMPLEXITY / LONG FUNCTIONS")
            print("-"*60)
            
            for filename, func in summary['problem_functions']:
                print(f"{filename}::{func.name}")
                print(f"  Lines: {func.line_count}, Complexity: {func.complexity}")
                if func.complexity > 15:
                    print("  WARNING: HIGH COMPLEXITY - Consider refactoring")
                if func.line_count > 100:
                    print("  WARNING: VERY LONG - Consider breaking into smaller functions")
        
        # Large classes
        if summary['large_classes']:
            print("\n" + "-"*60)
            print("LARGE CLASSES")
            print("-"*60)
            
            for filename, cls in summary['large_classes']:
                print(f"{filename}::{cls.name}")
                print(f"  Lines: {cls.line_count}, Methods: {cls.methods}")
        
        # Recommendations
        print("\n" + "-"*60)
        print("RECOMMENDATIONS")
        print("-"*60)
        
        recommendations = []
        
        # Check MOP.py size
        mop_analysis = next((f for f in self.file_analyses if f.filename == 'MOP.py'), None)
        if mop_analysis and mop_analysis.line_count > 1000:
            recommendations.append(
                f"1. MOP.py ({mop_analysis.line_count} lines) is very large. "
                "Consider splitting into separate modules for different gear types."
            )
        
        # Check for functions without docstrings
        undocumented_funcs = 0
        for file_analysis in self.file_analyses:
            for func in file_analysis.functions:
                if not func.docstring and not func.name.startswith('_'):
                    undocumented_funcs += 1
        
        if undocumented_funcs > 0:
            recommendations.append(
                f"2. {undocumented_funcs} public functions lack docstrings. "
                "Add comprehensive documentation for better maintainability."
            )
        
        # Check complexity
        high_complexity_files = [f for f in self.file_analyses if f.complexity_score > 50]
        if high_complexity_files:
            recommendations.append(
                f"3. {len(high_complexity_files)} files have high complexity. "
                "Consider refactoring complex conditional logic."
            )
        
        # Check maintainability
        low_maintainability = [f for f in self.file_analyses if f.maintainability_index < 60]
        if low_maintainability:
            recommendations.append(
                f"4. {len(low_maintainability)} files have low maintainability scores. "
                "Focus on reducing complexity and improving structure."
            )
        
        if not recommendations:
            recommendations.append("1. Code structure looks good overall!")
        
        for rec in recommendations:
            print(rec)
        
        return summary

def main():
    """Run code structure analysis"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    analyzer = CodeAnalyzer(current_dir)
    analyzer.generate_report()

if __name__ == "__main__":
    main()