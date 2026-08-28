from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EntityType(StrEnum):
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    BRAND = "brand"
    MARKET = "market"
    INDUSTRY = "industry"
    LOCATION = "location"
    PROJECT = "project"
    TENDER = "tender"
    TECHNOLOGY = "technology"


class EntityBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1, max_length=200)
    entity_type: EntityType
    name: str = Field(min_length=1, max_length=500)

    source_url: HttpUrl | None = None
    observed_at: datetime = Field(default_factory=utc_now)

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    attributes: dict[str, Any] = Field(default_factory=dict)


class Company(EntityBase):
    entity_type: EntityType = EntityType.COMPANY

    legal_name: str | None = Field(default=None, max_length=500)
    website: HttpUrl | None = None

    industry: str | None = Field(default=None, max_length=300)
    country: str | None = Field(default=None, max_length=200)
    region: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=200)

    employee_count: int | None = Field(default=None, ge=0)
    employee_count_min: int | None = Field(default=None, ge=0)
    employee_count_max: int | None = Field(default=None, ge=0)


class Person(EntityBase):
    entity_type: EntityType = EntityType.PERSON

    first_name: str | None = Field(default=None, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)

    job_title: str | None = Field(default=None, max_length=300)
    department: str | None = Field(default=None, max_length=300)
    seniority: str | None = Field(default=None, max_length=100)

    company_id: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=300)


class Product(EntityBase):
    entity_type: EntityType = EntityType.PRODUCT

    sku: str | None = Field(default=None, max_length=200)
    brand_id: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=300)

    description: str | None = Field(default=None, max_length=10_000)

    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price: float | None = Field(default=None, ge=0.0)

    availability: str | None = Field(default=None, max_length=100)


class Brand(EntityBase):
    entity_type: EntityType = EntityType.BRAND

    website: HttpUrl | None = None
    country: str | None = Field(default=None, max_length=200)


class Market(EntityBase):
    entity_type: EntityType = EntityType.MARKET

    industry: str | None = Field(default=None, max_length=300)
    geography: str | None = Field(default=None, max_length=300)

    market_size: float | None = Field(default=None, ge=0.0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class Industry(EntityBase):
    entity_type: EntityType = EntityType.INDUSTRY


class Location(EntityBase):
    entity_type: EntityType = EntityType.LOCATION

    country: str | None = Field(default=None, max_length=200)
    region: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=200)


class Project(EntityBase):
    entity_type: EntityType = EntityType.PROJECT

    company_id: str | None = Field(default=None, max_length=200)
    location_id: str | None = Field(default=None, max_length=200)

    status: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=10_000)


class Tender(EntityBase):
    entity_type: EntityType = EntityType.TENDER

    issuing_organization: str | None = Field(default=None, max_length=500)
    reference_number: str | None = Field(default=None, max_length=200)

    closing_at: datetime | None = None
    status: str | None = Field(default=None, max_length=100)


class Technology(EntityBase):
    entity_type: EntityType = EntityType.TECHNOLOGY

    category: str | None = Field(default=None, max_length=300)
    vendor: str | None = Field(default=None, max_length=500)
