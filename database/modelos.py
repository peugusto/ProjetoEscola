"""
Modelagem relacional com SQLAlchemy (ORM).

Esquema em estrela:
  dim_regiao  1 ── n  dim_estado  1 ── n  dim_municipio
  dim_disciplina
  fato_avaliacao  (métricas por período, município, rede e disciplina)
"""
from __future__ import annotations

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Regiao(Base):
    __tablename__ = "dim_regiao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    estados: Mapped[list["Estado"]] = relationship(back_populates="regiao")


class Estado(Base):
    __tablename__ = "dim_estado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(40), nullable=False)
    codigo_ibge: Mapped[int | None] = mapped_column(Integer, nullable=True)
    regiao_id: Mapped[int] = mapped_column(ForeignKey("dim_regiao.id"), nullable=False)

    regiao: Mapped[Regiao] = relationship(back_populates="estados")
    municipios: Mapped[list["Municipio"]] = relationship(back_populates="estado")


class Municipio(Base):
    __tablename__ = "dim_municipio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    estado_id: Mapped[int] = mapped_column(ForeignKey("dim_estado.id"), nullable=False)

    estado: Mapped[Estado] = relationship(back_populates="municipios")
    avaliacoes: Mapped[list["Avaliacao"]] = relationship(back_populates="municipio")


class Disciplina(Base):
    __tablename__ = "dim_disciplina"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    avaliacoes: Mapped[list["Avaliacao"]] = relationship(back_populates="disciplina")


class Avaliacao(Base):
    __tablename__ = "fato_avaliacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semestre: Mapped[int] = mapped_column(Integer, nullable=False)
    data = mapped_column(Date, nullable=False)
    rede_ensino: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    municipio_id: Mapped[int] = mapped_column(ForeignKey("dim_municipio.id"), nullable=False, index=True)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("dim_disciplina.id"), nullable=False, index=True)

    media_notas: Mapped[float] = mapped_column(Float, nullable=False)
    taxa_aprovacao: Mapped[float] = mapped_column(Float, nullable=False)
    taxa_reprovacao: Mapped[float] = mapped_column(Float, nullable=False)
    acesso_internet: Mapped[float] = mapped_column(Float, nullable=False)
    renda_media_familiar: Mapped[float] = mapped_column(Float, nullable=False)
    indice_desempenho: Mapped[float] = mapped_column(Float, nullable=False)
    nivel_desempenho: Mapped[str] = mapped_column(String(10), nullable=False)
    nivel_calculado: Mapped[str] = mapped_column(String(10), nullable=False)
    taxas_inconsistentes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    municipio: Mapped[Municipio] = relationship(back_populates="avaliacoes")
    disciplina: Mapped[Disciplina] = relationship(back_populates="avaliacoes")
