from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Enum, ForeignKey, Table
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

# ---------------- ENUMS ---------------- #
class VulnerabilityStatus(enum.Enum):
    Affected = "Affected"
    NotAffected = "NotAffected"

class TestStatus(enum.Enum):
    Created = "Created"
    ErrorGenerating = "ErrorGenerating"
    ErrorBuilding = "ErrorBuilding"
    ErrorExecuting = "ErrorExecuting"
    Vulnerable = "Vulnerable"
    NotVulnerable = "NotVulnerable"

# ---------------- ASSOCIATION TABLES ---------------- #
# Relación muchos-a-muchos entre Vulnerability y CWE
vulnerability_cwe = Table(
    "vulnerability_cwe",
    Base.metadata,
    Column("vulnerability_id", Integer, ForeignKey("vulnerability.id"), primary_key=True),
    Column("cwe_id", Integer, ForeignKey("cwe.id"), primary_key=True),
)

# ---------------- ENTIDADES ---------------- #
class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    pomPath = Column(String)

    # Relación: un proyecto tiene muchos scanners
    scanners = relationship("Scanner", back_populates="project")

class Scanner(Base):
    __tablename__ = "scanner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)

    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship("Project", back_populates="scanners")

    # Relación: un scanner encuentra muchas vulnerabilidades
    vulnerabilities = relationship("Vulnerability", back_populates="scanner")

class CWE(Base):
    __tablename__ = "cwe"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    vulnerabilities = relationship(
        "Vulnerability",
        secondary=vulnerability_cwe,
        back_populates="cwes"
    )

class Vulnerability(Base):
    __tablename__ = "vulnerability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    CVE = Column(String)
    impact = Column(Float)
    attackVector = Column(String)
    status = Column(String)

    scanner_id = Column(Integer, ForeignKey("scanner.id"))
    scanner = relationship("Scanner", back_populates="vulnerabilities")

    cwes = relationship(
        "CWE",
        secondary=vulnerability_cwe,
        back_populates="vulnerabilities"
    )

    artifacts = relationship("Artifact", back_populates="vulnerability")

class Artifact(Base):
    __tablename__ = "artifact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filePath = Column(String)
    name = Column(String)
    line = Column(Integer)
    affected = Column(Enum(VulnerabilityStatus))

    vulnerability_id = Column(Integer, ForeignKey("vulnerability.id"))
    vulnerability = relationship("Vulnerability", back_populates="artifacts")

    fuzzer_id = Column(Integer, ForeignKey("fuzzer.id"))
    fuzzer = relationship("Fuzzer", back_populates="artifacts")

class Fuzzer(Base):
    __tablename__ = "fuzzer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testPath = Column(String)
    name = Column(String)
    status = Column(Enum(TestStatus))
    stackLevel = Column(Integer)

    artifacts = relationship("Artifact", back_populates="fuzzer")
