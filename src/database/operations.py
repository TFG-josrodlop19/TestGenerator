from .setup import get_session
from database.models import *
from sqlalchemy.orm import joinedload


def find_last_scanner_confidence(owner: str, name: str):
    """Buscar un proyecto específico"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if last_scanner:
            return last_scanner.confidence
        else:
            raise ValueError("No scanner found for the given project.")

def create_project(owner: str, name: str, pom_path: str, confidence: ConfidenceLevel) -> Project:
    """
    Creates or updates a project in the database (lazy loading).
    """
    new_scanner = Scanner(
        date=datetime.now(),
        confidence=confidence
    )
    with get_session() as session:
        existing_project = session.query(Project).options(
            joinedload(Project.scanners)
        ).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if existing_project:
            if pom_path:
                existing_project.pomPath = pom_path
                existing_project.scanners.append(new_scanner)
                session.commit()
                session.refresh(existing_project)
            
            return existing_project
        else:
            # If not exists, create new project
            new_project = Project(
                owner=owner,
                name=name,
                pomPath=pom_path
            )
            new_project.scanners.append(new_scanner)
            session.add(new_project)
            session.commit()
            session.refresh(new_project)
            
            return new_project


def create_vulnerabilities_artifacts(project_id: int, vulnerabilities: list[Vulnerability]):
    """Creates vulnerabilities and artifacts in the database for an existing project and scanner"""
    with get_session() as session:
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project_id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        scanner_id = last_scanner.id
        for vulnerability in vulnerabilities:            
            vulnerability.scanner_id = scanner_id
            session.add(vulnerability)
            for artifact in vulnerability.artifacts:
                session.add(artifact)
        session.commit()


def find_fuzzer_by_scanner_fuzzer(session, scanner_id: int, fuzzer_name: str, fuzzer_testPath: str) -> Fuzzer:
    """Auxiliar function to find a fuzzer by its name and testPath within the context of a specific scanner.
    
    Keyword arguments:
    scanner_id -- ID of the scanner
    fuzzer_name -- Name of the fuzzer
    fuzzer_testPath -- Test path of the fuzzer
    Return: Fuzzer object or None
    """
    
    fuzzer = session.query(Fuzzer).join(
        artifact_fuzzer, Fuzzer.id == artifact_fuzzer.c.fuzzer_id
    ).join(
        Artifact, artifact_fuzzer.c.artifact_id == Artifact.id
    ).join(
        vulnerability_artifact, Artifact.id == vulnerability_artifact.c.artifact_id
    ).join(
        Vulnerability, vulnerability_artifact.c.vulnerability_id == Vulnerability.id
    ).filter(
        Vulnerability.scanner_id == scanner_id,
        fuzzer_name == Fuzzer.name,
        fuzzer_testPath == Fuzzer.testPath
    ).first()
        
    return fuzzer

def find_artifacts_with_no_fuzzers(owner: str, project_name: str):
    """Find artifacts that have no associated fuzzers for a specific project"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == project_name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        
        artifacts_with_no_fuzzers = session.query(Artifact).join(
            vulnerability_artifact, Artifact.id == vulnerability_artifact.c.artifact_id
        ).join(
            Vulnerability, vulnerability_artifact.c.vulnerability_id == Vulnerability.id
        ).outerjoin(
            artifact_fuzzer, Artifact.id == artifact_fuzzer.c.artifact_id
        ).filter(
            Vulnerability.scanner_id == last_scanner.id,
            artifact_fuzzer.c.fuzzer_id.is_(None)  # 👈 CONDICIÓN CORRECTA
        ).all()

    return artifacts_with_no_fuzzers

def save_artifacts_fuzzer(owner: str, project_name: str, artifact: Artifact):
    """Saves one artifact's fuzzers in the database"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == project_name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        
        # Find artifact associated with the last scanner's vulnerabilities
        matching_artifact = session.query(Artifact).options(
            joinedload(Artifact.fuzzers)
        ).join(
            vulnerability_artifact, Artifact.id == vulnerability_artifact.c.artifact_id
        ).join(
            Vulnerability, vulnerability_artifact.c.vulnerability_id == Vulnerability.id
        ).filter(
            Vulnerability.scanner_id == last_scanner.id,
            Artifact.filePath == artifact.filePath,
            Artifact.name == artifact.name,
            Artifact.line == artifact.line
        ).first()
        

        if not matching_artifact:
            raise ValueError("No matching artifact found.")
        
        matching_artifact = session.merge(matching_artifact)
        
        for fuzzer in artifact.fuzzers:
            # Check if fuzzer already exists in the context of the last scanner to avoid duplicates
            matching_fuzzer = find_fuzzer_by_scanner_fuzzer(session, last_scanner.id, fuzzer.name, fuzzer.testPath)
            if matching_fuzzer:
                matching_fuzzer = session.merge(matching_fuzzer)
                if matching_fuzzer not in matching_artifact.fuzzers:
                    matching_artifact.fuzzers.add(matching_fuzzer)
            else:
                # Create new fuzzer instance before adding to avoid duplicates (sqlalchemy issue)
                new_fuzzer = Fuzzer(
                    name=fuzzer.name,
                    status=fuzzer.status,
                    testPath=fuzzer.testPath,
                    usesParameters=fuzzer.usesParameters,
                    artifactPath=fuzzer.artifactPath,
                    artifactName=fuzzer.artifactName,
                    artifactLine=fuzzer.artifactLine
                )
                session.add(new_fuzzer)
                session.flush()
                matching_artifact.fuzzers.add(new_fuzzer)
        session.commit()


def get_created_fuzzers_by_project(owner: str, project_name: str) -> list[Fuzzer]:
    """Retrieve all created fuzzers for a given project"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == project_name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        
        fuzzers = session.query(Fuzzer).join(
            artifact_fuzzer, Fuzzer.id == artifact_fuzzer.c.fuzzer_id
        ).join(
            Artifact, artifact_fuzzer.c.artifact_id == Artifact.id
        ).join(
            vulnerability_artifact, Artifact.id == vulnerability_artifact.c.artifact_id
        ).join(
            Vulnerability, vulnerability_artifact.c.vulnerability_id == Vulnerability.id
        ).filter(
            Vulnerability.scanner_id == last_scanner.id,
            Fuzzer.status == TestStatus.CREATED
        ).all()
        
    return fuzzers

def find_fuzzers_with_errors(owner: str, project_name: str):
    """Find all fuzzers with errors for a specific project for the last scanner.
    Keyword arguments:
    owner -- Owner of the GitHub repository
    project_name -- Name of the GitHub repository
    Return: List of Fuzzer objects with errors
    """
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == project_name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        
        fuzzers = session.query(Fuzzer).join(
            artifact_fuzzer, Fuzzer.id == artifact_fuzzer.c.fuzzer_id
        ).join(
            Artifact, artifact_fuzzer.c.artifact_id == Artifact.id
        ).join(
            vulnerability_artifact, Artifact.id == vulnerability_artifact.c.artifact_id
        ).join(
            Vulnerability, vulnerability_artifact.c.vulnerability_id == Vulnerability.id
        ).filter(
            Vulnerability.scanner_id == last_scanner.id,
            Fuzzer.status == TestStatus.ERROR_BUILDING or 
            Fuzzer.status == TestStatus.ERROR_EXECUTING or 
            Fuzzer.status == TestStatus.ERROR_GENERATING
        ).all()
        
    return fuzzers
    
def update_fuzzer_status(fuzzer_id: int, new_status: TestStatus, crash_info: dict=None):
    """Update the status of a fuzzer"""
    with get_session() as session:
        fuzzer = session.query(Fuzzer).filter(Fuzzer.id == fuzzer_id).first()
        if not fuzzer:
            raise ValueError("Fuzzer not found.")
        
        fuzzer.status = new_status
        if crash_info:
            fuzzer.crashType = crash_info.get("type")
            fuzzer.crashDescription = crash_info.get("description")
        session.commit()
        
def update_states_after_execution(owner: str, name: str):
    """Update the states of fuzzers after execution"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        last_scanner = session.query(Scanner).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
        if not last_scanner:
            raise ValueError("No scanner found for the given project.")
        
        vulnerabilities = session.query(Vulnerability).options(
            joinedload(Vulnerability.artifacts).joinedload(Artifact.fuzzers)
        ).filter(
            Vulnerability.scanner_id == last_scanner.id
        ).all()
        
        for vulnerability in vulnerabilities:
            vulnerability_affected = False
            vulnerability_has_artifacts_with_fuzzers =  False
            
            for artifact in vulnerability.artifacts:
                if not artifact.fuzzers or len(artifact.fuzzers) == 0:
                    continue  # Skip artifacts without fuzzers
                
                # Check if any fuzzer is vulnerable
                has_vulnerable_fuzzer = any(
                    fuzzer.status == TestStatus.VULNERABLE 
                    for fuzzer in artifact.fuzzers
                )
                tested = any(
                    fuzzer.status in [TestStatus.VULNERABLE, TestStatus.NOT_VULNERABLE]
                    for fuzzer in artifact.fuzzers
                )
                
                if has_vulnerable_fuzzer:
                    artifact.affected = VulnerabilityStatus.AFFECTED
                    vulnerability_affected = True
                    vulnerability_has_artifacts_with_fuzzers = True
                elif tested:
                    artifact.affected = VulnerabilityStatus.NOT_AFFECTED
                    vulnerability_has_artifacts_with_fuzzers = True
                else:
                    artifact.affected = VulnerabilityStatus.UNKNOWN
                
                session.add(artifact)
            
            # Update vulnerability status based on artifacts' affected status
            if vulnerability_has_artifacts_with_fuzzers:
                vulnerability.status = (
                    VulnerabilityStatus.AFFECTED if vulnerability_affected 
                    else VulnerabilityStatus.NOT_AFFECTED
                )
            
            session.add(vulnerability)
        
        session.commit()


def get_last_scanner_all_data_by_project(owner: str, name: str):
    """Get all scanner data for a specific project"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")

        last_scanner = session.query(Scanner).options(
            joinedload(Scanner.vulnerabilities).joinedload(Vulnerability.artifacts).joinedload(Artifact.fuzzers)
        ).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
    return last_scanner

def get_last_scanner_data_by_project(owner: str, name: str):
    """Get basic scanner data for a specific project avoiding UNKNOWN statuses"""
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")

        last_scanner = session.query(Scanner).options(
            joinedload(Scanner.vulnerabilities.and_(
                Vulnerability.status != VulnerabilityStatus.UNKNOWN
            )).joinedload(Vulnerability.artifacts.and_(
                Artifact.affected != VulnerabilityStatus.UNKNOWN
            )).joinedload(Artifact.fuzzers),
            joinedload(Scanner.vulnerabilities.and_(
                Vulnerability.status != VulnerabilityStatus.UNKNOWN
            ))
        ).filter(
            Scanner.project_id == project.id
        ).order_by(Scanner.date.desc()).first()
        
    return last_scanner

def get_scanner_by_id(scanner_id: int):
    """Get scanner by its ID avoiding UNKNOWN statuses"""
    with get_session() as session:
        scanner = session.query(Scanner).options(
            joinedload(Scanner.vulnerabilities.and_(
                Vulnerability.status != VulnerabilityStatus.UNKNOWN
            )).joinedload(Vulnerability.artifacts.and_(
                Artifact.affected != VulnerabilityStatus.UNKNOWN
            )).joinedload(Artifact.fuzzers),
            joinedload(Scanner.vulnerabilities.and_(
                Vulnerability.status != VulnerabilityStatus.UNKNOWN
            ))
        ).filter(
            Scanner.id == scanner_id
        ).first()

    return scanner


def get_scanner_all_data_by_id(scanner_id: int):
    """Get all scanner data by its ID"""
    with get_session() as session:
        scanner = session.query(Scanner).options(
            joinedload(Scanner.vulnerabilities).joinedload(Vulnerability.artifacts).joinedload(Artifact.fuzzers),
            joinedload(Scanner.vulnerabilities)
        ).filter(
            Scanner.id == scanner_id
        ).first()

    return scanner


def get_scanners_by_project(owner: str, name: str, num: int) -> list[Scanner]:
    """
    Retrieve scanners for a given project
    If num is -1 or 0, retrieve all scanners
    """
    with get_session() as session:
        project = session.query(Project).filter(
            Project.owner == owner,
            Project.name == name
        ).first()
        
        if not project:
            raise ValueError("Project not found.")
        
        if num and num > 0:
            scanners = session.query(Scanner).filter(
                Scanner.project_id == project.id
            ).order_by(Scanner.date.desc()).limit(num).all()
        else:
            scanners = session.query(Scanner).filter(
                Scanner.project_id == project.id
            ).order_by(Scanner.date.desc()).all()

    return scanners