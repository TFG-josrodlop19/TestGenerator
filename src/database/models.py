from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Enum, ForeignKey, Table, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
import enum
class Base(DeclarativeBase):
    pass

# Enums
class ConfidenceLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ABSOLUTE = "absolute"
    
    def get_timeout_seconds(self):
        """Returns the timeout in seconds for each confidence level"""
        timeouts = {
            ConfidenceLevel.LOW: 120,
            ConfidenceLevel.MEDIUM: 600,
            ConfidenceLevel.HIGH: 3600,
            ConfidenceLevel.ABSOLUTE: None  # No limit
        }
        return timeouts[self]
    
class VulnerabilityStatus(enum.Enum):
    AFFECTED = "affected"
    NOT_AFFECTED = "not_affected"
    UNKNOWN = "unknown"
    
class TestStatus(enum.Enum):
    CREATED = "Created"
    ERROR_BUILDING = "Error building"
    ERROR_EXECUTING = "Error executing"
    ERROR_GENERATING = "Error generating"
    VULNERABLE = "Vulnerable"
    NOT_VULNERABLE = "Not vulnerable"

# Association tables
vulnerability_cwe = Table(
    "vulnerability_cwe",
    Base.metadata,
    Column("vulnerability_id", ForeignKey("vulnerability.id"), primary_key=True),
    Column("cwe_id",ForeignKey("cwe.id"), primary_key=True),
)

vulnerability_artifact = Table(
    "vulnerability_artifact",
    Base.metadata,
    Column("vulnerability_id", ForeignKey("vulnerability.id"), primary_key=True),
    Column("artifact_id", ForeignKey("artifact.id"), primary_key=True),
)

artifact_fuzzer = Table(
    "artifact_fuzzer",
    Base.metadata,
    Column("artifact_id", ForeignKey("artifact.id"), primary_key=True),
    Column("fuzzer_id", ForeignKey("fuzzer.id"), primary_key=True),
)

# ---------------- ENTIDADES ---------------- #
class Project(Base):
    __tablename__ = "project"
    __table_args__ = (UniqueConstraint("owner", "name", name="pk_owner_name"),)
    
    #PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    
    #Attibutes
    pomPath: Mapped[str] = mapped_column(nullable=False)
    
    #FK
    scanners: Mapped[list["Scanner"]] = relationship()
class Scanner(Base):
    __tablename__ = "scanner"
    
    #PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    #Attributes
    date: Mapped[datetime]
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel), nullable=False)

    #FK
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship()


class CWE(Base):
    __tablename__ = "cwe"
    #PK
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    #Attributes
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

class Vulnerability(Base):
    __tablename__ = "vulnerability"
    
    #PK
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    #Attributes
    name : Mapped[str]
    impact : Mapped[float]
    attackVector : Mapped[str]
    status : Mapped[VulnerabilityStatus] = mapped_column(Enum(VulnerabilityStatus), default=VulnerabilityStatus.UNKNOWN)

    #FK
    cwes: Mapped[list["CWE"]] = relationship(secondary=vulnerability_cwe)
    scanner_id: Mapped[int] = mapped_column(ForeignKey("scanner.id"))
    artifacts: Mapped[set["Artifact"]] = relationship(secondary=vulnerability_artifact, back_populates="vulnerabilities") 
    

class Artifact(Base):
    __tablename__ = "artifact"

    #PK
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    #Attributes
    filePath: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    affected: Mapped[VulnerabilityStatus] = mapped_column(Enum(VulnerabilityStatus), nullable=False, default=VulnerabilityStatus.UNKNOWN)

    #FK
    vulnerabilities: Mapped[set["Vulnerability"]] = relationship(secondary=vulnerability_artifact, back_populates="artifacts")
    fuzzers: Mapped[set["Fuzzer"]] = relationship(secondary=artifact_fuzzer, back_populates="artifacts")

class Fuzzer(Base):
    __tablename__ = "fuzzer"

    #PK
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    #Attributes
    testPath: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    artifactPath: Mapped[str] = mapped_column(String, nullable=False)
    artifactName: Mapped[str] = mapped_column(String, nullable=False)
    artifactLine: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TestStatus] = mapped_column(Enum(TestStatus))
    usesParameters: Mapped[bool] = mapped_column(nullable=False, default=True)
    crashType: Mapped[str] = mapped_column(String, nullable=True)
    crashDescription: Mapped[str] = mapped_column(String, nullable=True)

    # FK
    artifacts: Mapped[set["Artifact"]] = relationship(secondary=artifact_fuzzer, back_populates="fuzzers")
