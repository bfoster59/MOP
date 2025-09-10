#!/usr/bin/env python3
"""
Security and Input Validation Analysis for MOP Gear Metrology System
Identifies potential security vulnerabilities and validation issues
"""

import ast
import os
import re
from typing import Dict, List, Any, Set
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    severity: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    category: str
    description: str
    file: str
    line: int
    recommendation: str

class SecurityAnalyzer:
    """Analyze security vulnerabilities and input validation issues"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.issues: List[SecurityIssue] = []
        
    def analyze_file(self, filepath: str) -> List[SecurityIssue]:
        """Analyze a single file for security issues"""
        issues = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        filename = os.path.basename(filepath)
        
        # Check for various security issues
        issues.extend(self._check_input_validation(tree, lines, filename))
        issues.extend(self._check_file_operations(tree, lines, filename))
        issues.extend(self._check_command_injection(content, lines, filename))
        issues.extend(self._check_path_traversal(content, lines, filename))
        issues.extend(self._check_exception_handling(tree, lines, filename))
        issues.extend(self._check_api_security(tree, lines, filename))
        issues.extend(self._check_data_exposure(tree, lines, filename))
        
        return issues
    
    def _check_input_validation(self, tree: ast.AST, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for insufficient input validation"""
        issues = []
        
        # Look for functions that take user input without validation
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has user input parameters but no validation
                if self._has_user_input_params(node) and not self._has_input_validation(node):
                    issues.append(SecurityIssue(
                        severity="MEDIUM",
                        category="Input Validation",
                        description=f"Function '{node.name}' accepts user input without validation",
                        file=filename,
                        line=node.lineno,
                        recommendation="Add input validation for all user-supplied parameters"
                    ))
        
        # Check for missing range checks on critical calculations
        for i, line in enumerate(lines, 1):
            if any(op in line for op in ['/', '//', '%', '**']):
                if 'if' not in line and 'assert' not in line:
                    # Check if there's a division that could cause division by zero
                    if '/' in line and 'zero' not in line.lower():
                        issues.append(SecurityIssue(
                            severity="MEDIUM", 
                            category="Division by Zero",
                            description="Potential division by zero without validation",
                            file=filename,
                            line=i,
                            recommendation="Add zero checks before division operations"
                        ))
        
        return issues
    
    def _check_file_operations(self, tree: ast.AST, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for unsafe file operations"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() calls without proper error handling
                if (isinstance(node.func, ast.Name) and node.func.id == 'open') or \
                   (isinstance(node.func, ast.Attribute) and node.func.attr == 'open'):
                    
                    # Check if it's in a try-except block
                    parent = self._find_parent_try(tree, node)
                    if not parent:
                        issues.append(SecurityIssue(
                            severity="LOW",
                            category="File Operations",
                            description="File open operation without exception handling",
                            file=filename,
                            line=node.lineno,
                            recommendation="Wrap file operations in try-except blocks"
                        ))
                    
                    # Check for unsafe file modes
                    if len(node.args) > 1:
                        mode_arg = node.args[1]
                        if isinstance(mode_arg, ast.Str) and 'w' in mode_arg.s:
                            issues.append(SecurityIssue(
                                severity="LOW",
                                category="File Operations", 
                                description="File opened in write mode - potential data loss",
                                file=filename,
                                line=node.lineno,
                                recommendation="Consider backup strategies for write operations"
                            ))
        
        return issues
    
    def _check_command_injection(self, content: str, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for potential command injection vulnerabilities"""
        issues = []
        
        # Look for subprocess calls, os.system, eval, exec
        dangerous_functions = ['subprocess', 'os.system', 'eval', 'exec', 'compile']
        
        for i, line in enumerate(lines, 1):
            for func in dangerous_functions:
                if func in line:
                    issues.append(SecurityIssue(
                        severity="HIGH" if func in ['eval', 'exec'] else "MEDIUM",
                        category="Command Injection",
                        description=f"Use of potentially dangerous function: {func}",
                        file=filename,
                        line=i,
                        recommendation=f"Avoid {func} or ensure input is properly sanitized"
                    ))
        
        return issues
    
    def _check_path_traversal(self, content: str, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for path traversal vulnerabilities"""
        issues = []
        
        # Look for path operations that might be vulnerable
        path_patterns = [
            r'\.\./',  # Directory traversal
            r'\.\.\\', # Windows directory traversal
            r'/etc/',  # Unix system files
            r'C:\\',   # Windows system paths
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in path_patterns:
                if re.search(pattern, line):
                    issues.append(SecurityIssue(
                        severity="MEDIUM",
                        category="Path Traversal",
                        description=f"Potential path traversal pattern: {pattern}",
                        file=filename,
                        line=i,
                        recommendation="Validate and sanitize file paths"
                    ))
        
        return issues
    
    def _check_exception_handling(self, tree: ast.AST, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for poor exception handling practices"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check for bare except clauses
                if node.type is None:
                    issues.append(SecurityIssue(
                        severity="MEDIUM",
                        category="Exception Handling",
                        description="Bare except clause can hide errors",
                        file=filename,
                        line=node.lineno,
                        recommendation="Catch specific exceptions instead of using bare except"
                    ))
                
                # Check for exceptions that print sensitive information
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id == 'print':
                            issues.append(SecurityIssue(
                                severity="LOW",
                                category="Information Disclosure",
                                description="Exception handler prints information that might be sensitive",
                                file=filename,
                                line=child.lineno,
                                recommendation="Log errors securely instead of printing"
                            ))
        
        return issues
    
    def _check_api_security(self, tree: ast.AST, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for API security issues"""
        issues = []
        
        # Check for API endpoints without authentication
        if 'api' in filename.lower():
            for i, line in enumerate(lines, 1):
                if '@app.' in line and 'post' in line.lower():
                    # Look for authentication decorators in surrounding lines
                    auth_found = False
                    for j in range(max(0, i-5), min(len(lines), i+2)):
                        if any(auth in lines[j].lower() for auth in ['auth', 'token', 'login', 'security']):
                            auth_found = True
                            break
                    
                    if not auth_found:
                        issues.append(SecurityIssue(
                            severity="MEDIUM",
                            category="API Security",
                            description="API endpoint without apparent authentication",
                            file=filename,
                            line=i,
                            recommendation="Add authentication/authorization to API endpoints"
                        ))
                
                # Check for CORS issues
                if 'cors' in line.lower() and '*' in line:
                    issues.append(SecurityIssue(
                        severity="MEDIUM",
                        category="CORS",
                        description="CORS allows all origins (*)",
                        file=filename,
                        line=i,
                        recommendation="Restrict CORS to specific trusted origins"
                    ))
        
        return issues
    
    def _check_data_exposure(self, tree: ast.AST, lines: List[str], filename: str) -> List[SecurityIssue]:
        """Check for potential data exposure issues"""
        issues = []
        
        # Look for hardcoded secrets or sensitive data
        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        severity="HIGH",
                        category="Data Exposure",
                        description=description,
                        file=filename,
                        line=i,
                        recommendation="Move sensitive data to environment variables or config files"
                    ))
        
        return issues
    
    def _has_user_input_params(self, func_node: ast.FunctionDef) -> bool:
        """Check if function accepts user input parameters"""
        # Simple heuristic: functions with certain parameter names or patterns
        user_input_indicators = ['request', 'params', 'data', 'input', 'args', 'kwargs']
        
        for arg in func_node.args.args:
            if any(indicator in arg.arg.lower() for indicator in user_input_indicators):
                return True
        
        return False
    
    def _has_input_validation(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has input validation"""
        # Look for validation patterns in function body
        validation_indicators = ['validate', 'check', 'assert', 'raise', 'ValueError', 'TypeError']
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and any(indicator in node.id for indicator in validation_indicators):
                return True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if any(indicator in node.func.id for indicator in validation_indicators):
                    return True
        
        return False
    
    def _find_parent_try(self, tree: ast.AST, target_node: ast.AST) -> ast.Try:
        """Find if a node is inside a try block"""
        # This is a simplified check - in practice, you'd need proper AST traversal
        # For now, just return None as it's complex to implement properly
        return None
    
    def analyze_all_files(self) -> Dict[str, Any]:
        """Analyze all Python files in the project"""
        all_issues = []
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    file_issues = self.analyze_file(filepath)
                    all_issues.extend(file_issues)
        
        self.issues = all_issues
        return self._generate_security_summary()
    
    def _generate_security_summary(self) -> Dict[str, Any]:
        """Generate security analysis summary"""
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        category_counts = {}
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        return {
            "total_issues": len(self.issues),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "issues": self.issues
        }
    
    def generate_report(self):
        """Generate comprehensive security report"""
        summary = self.analyze_all_files()
        
        print("="*80)
        print("SECURITY AND INPUT VALIDATION ANALYSIS REPORT")
        print("="*80)
        
        print(f"Total security issues found: {summary['total_issues']}")
        print(f"High severity: {summary['severity_breakdown']['HIGH']}")
        print(f"Medium severity: {summary['severity_breakdown']['MEDIUM']}")
        print(f"Low severity: {summary['severity_breakdown']['LOW']}")
        
        print("\nCategory Breakdown:")
        for category, count in summary['category_breakdown'].items():
            print(f"  {category}: {count}")
        
        # Group issues by severity
        high_issues = [i for i in self.issues if i.severity == "HIGH"]
        medium_issues = [i for i in self.issues if i.severity == "MEDIUM"]
        low_issues = [i for i in self.issues if i.severity == "LOW"]
        
        if high_issues:
            print("\n" + "="*60)
            print("HIGH SEVERITY ISSUES (Immediate attention required)")
            print("="*60)
            for issue in high_issues:
                print(f"\n{issue.file}:{issue.line}")
                print(f"  Category: {issue.category}")
                print(f"  Issue: {issue.description}")
                print(f"  Recommendation: {issue.recommendation}")
        
        if medium_issues:
            print("\n" + "="*60)
            print("MEDIUM SEVERITY ISSUES")
            print("="*60)
            for issue in medium_issues[:10]:  # Show first 10
                print(f"\n{issue.file}:{issue.line}")
                print(f"  Category: {issue.category}")
                print(f"  Issue: {issue.description}")
                print(f"  Recommendation: {issue.recommendation}")
            
            if len(medium_issues) > 10:
                print(f"\n... and {len(medium_issues) - 10} more medium severity issues")
        
        # Security recommendations
        print("\n" + "="*60)
        print("SECURITY RECOMMENDATIONS")
        print("="*60)
        
        recommendations = [
            "1. Implement comprehensive input validation for all user-supplied data",
            "2. Add authentication and authorization to API endpoints",
            "3. Use parameterized queries to prevent injection attacks",
            "4. Implement proper error handling without information disclosure",
            "5. Validate file paths to prevent path traversal attacks",
            "6. Use environment variables for sensitive configuration",
            "7. Add rate limiting to API endpoints",
            "8. Implement logging and monitoring for security events",
            "9. Regular security testing and code reviews",
            "10. Keep dependencies updated for security patches"
        ]
        
        for rec in recommendations:
            print(rec)
        
        # Specific recommendations for the gear metrology system
        print("\n" + "="*60)
        print("GEAR METROLOGY SPECIFIC RECOMMENDATIONS")
        print("="*60)
        
        gear_recommendations = [
            "1. Validate gear parameters (tooth count, pressure angle, etc.) against physical limits",
            "2. Implement bounds checking for all geometric calculations",
            "3. Add overflow protection for mathematical operations",
            "4. Sanitize file paths for CSV import/export operations",
            "5. Implement proper error messages without exposing internal details",
            "6. Add audit logging for calculation requests in production",
            "7. Consider implementing calculation result caching with proper invalidation",
            "8. Add input sanitization for UI components",
            "9. Validate units and conversion factors to prevent calculation errors",
            "10. Implement graceful degradation for edge cases"
        ]
        
        for rec in gear_recommendations:
            print(rec)

def main():
    """Run security analysis"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    analyzer = SecurityAnalyzer(current_dir)
    analyzer.generate_report()

if __name__ == "__main__":
    main()