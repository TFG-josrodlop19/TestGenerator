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
    
    def get_timeout_minutes(self):
        """Returns the timeout in minutes for each confidence level"""
        timeouts = {
            ConfidenceLevel.LOW: 2,
            ConfidenceLevel.MEDIUM: 10,
            ConfidenceLevel.HIGH: 60,
            ConfidenceLevel.ABSOLUTE: None  # No limit
        }
        return timeouts[self]
    
class VulnerabilityStatus(enum.Enum):
    AFFECTED = "affected"
    NOT_AFFECTED = "not_affected"
    UNKNOWN = "unknown"
    
class TestStatus(enum.Enum):
    CREATED = "created"
    ERROR_BUILDING = "error_building"
    ERROR_EXECUTING = "error_executing"
    ERROR_GENERATING = "error_generating"
    VULNERABLE = "vulnerable"
    NOT_VULNERABLE = "not_vulnerable"

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
    status: Mapped[TestStatus] = mapped_column(Enum(TestStatus))

    # FK
    artifacts: Mapped[set["Artifact"]] = relationship(secondary=artifact_fuzzer, back_populates="fuzzers")
