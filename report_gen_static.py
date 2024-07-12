from radon.visitors import ComplexityVisitor
from radon.metrics import mi_visit, mi_rank
from radon.raw import analyze
import subprocess
import sys

def static_analysis_string(file_path, iteration, task, create_new_controller, use_vision_api):
    code_analysis = analyze_code(file_path)
    pep8_analysis = pep_report(file_path)
    pep8_issues = check_pep8(file_path)
    return f"Static Code analysis for iteration {iteration}: \ntask: {task}, new controller: {create_new_controller}, vision: {use_vision_api} \ncode_analysis: {code_analysis} \npep8_analysis: {pep8_analysis} \npep8_issues: {pep8_issues}\n\n"

def static_analysis_json(file_path):
    code_analysis = analyze_code(file_path)
    pep8_analysis = pep_report(file_path)
    return {
        "code_complexity": code_analysis["average_complexity"],
        "code_maintainability_score": code_analysis["maintainability_score"],
        "code_density": code_analysis["code_density"], 
        "pep8_errors": pep8_analysis["errors"], 
        "pep8_warnings": pep8_analysis["warnings"]
    }

# Analyses the controller code using libraries
def analyze_code(file_path):
    # Load file to be analyzed
    with open(file_path) as f:
        source_code = f.read()

    # Analyze the raw metrics needed for MI calculation
    raw_metrics = analyze(source_code)
    
    # Calculate Maintainability Index without considering comments
    mi_score = mi_visit(source_code, raw_metrics.multi)
    # Translate the numerical score into a grade
    mi_grade = mi_rank(mi_score)

    # Calculate code density as LLOC/LOC
    if raw_metrics.loc > 0:  # Prevent division by zero
        code_density = raw_metrics.lloc / raw_metrics.loc
    else:
        code_density = 0

    # Analyze the complexity of the functions and methods in the file. 
    visitor = ComplexityVisitor.from_code(source_code)
    # Score Accumulator for finding the average.
    complexity_scores = [method.complexity for cls in visitor.classes for method in cls.methods]
    complexity_scores += [func.complexity for func in visitor.functions]

    average_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0

    return {
        "average_complexity": average_complexity,
        "maintainability_score": mi_score,
        "maintainability_grade": mi_grade,
        "code_density": code_density
    }

def check_pep8(file_path):
    try:
        result = subprocess.run([sys.executable, '-m', 'flake8', file_path], text=True, capture_output=True)
        
        if result.returncode == 0:
            return {"errors": [], "warnings": []}
        else:
            errors = []
            warnings = []
            issues = result.stdout.strip().split('\n')
            for issue in issues:
                if issue.startswith('E'):
                    errors.append(issue)
                else:
                    warnings.append(issue)
            return {"errors": errors, "warnings": warnings}
    except Exception as e:
        print(f"An error occurred while checking PEP 8 compliance: {e}")
        return None
    
def pep_report(file_path):
    pep8_results = check_pep8(file_path)
    return {"errors": len(pep8_results["errors"]), "warnings": len(pep8_results["warnings"])}

