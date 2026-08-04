"""Generic dataclass validation used by the Dagster pipeline's validated_nasa_data asset.

Validates primary keys only — the dataclasses here check that pl_name/hostname (or
equivalent PK fields) exist and are populated; broader schema validation is dbt's job
downstream.
"""

import logging
from dataclasses import dataclass, field, fields
from typing import Any, TypeVar

import pandas as pd

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


@dataclass
class ExoplanetRecord:
    """Primary-key schema for a raw NASA exoplanet record."""

    pl_name: str = field(metadata={"pk": True})
    hostname: str = field(metadata={"pk": True})


# Bind typevar to DataClassInstance so pylance knows the input is guaranteed to be a valid dataclass
T = TypeVar("T", bound=Any)


def parse_row(row: dict, data_class: type[T]) -> T:
    """Parse a dataframe row and validate pks against the appropriate dataclass.

    Args:
        row (dict): Dataframe row.
        data_class (type[T]): The generic dataclass schema.

    Returns:
        T: Appropriate Dataclass object.

    Raises:
        ValueError: If primary key columns are blank or missing entirely.
    """
    # 1. Identify all primary key fields defined in the dataclass
    pk_cols = [f.name for f in fields(data_class) if f.metadata.get("pk")]

    if not pk_cols:
        logging.error("No primary key metadata configuration found in the dataclass!")
        raise ValueError("Data structure missing primary key metadata configuration.")

    # 2. Check that every PK column is present in the file and populated
    for pk in pk_cols:
        val = row.get(pk)
        if val is None or pd.isna(val) or str(val).strip() == "":
            logging.error(f"Primary key column '{pk}' is blank or missing from data!")
            raise ValueError(f"Primary key column '{pk}' cannot be blank.")

    return data_class(
        **{k: v for k, v in row.items() if k in {f.name for f in fields(data_class)}}
    )


def validate_records(
    df: pd.DataFrame, data_class: type[T]
) -> tuple[list[T], list[dict]]:
    """Validate dataframe records against the corresponding dataclass.

    Args:
        df (pd.DataFrame): Pandas dataframe with raw source data.
        data_class (type[T]): The generic dataclass schema.

    Returns:
        tuple[list[T], list[dict]]: Lists of valid and invalid record dicts.

    Raises:
        ValueError: If error parsing and appending row.
        TypeError: If error parsing and appending row.
        KeyError: If error parsing and appending row.
    """

    row_dictionaries = df.to_dict(orient="records")

    valid_records = []
    invalid_records = []

    for row in row_dictionaries:
        try:
            parse_row(row, data_class)  # validate only, don't use the return value
            valid_records.append(row)  # append the original full row, not the dataclass
        except (ValueError, TypeError, KeyError) as e:
            logging.warning(f"Row validation failed: {e}")
            row_with_error = row.copy()
            row_with_error["__validation_error__"] = str(e)
            invalid_records.append(row_with_error)

    logging.info(
        f"Validation complete — Valid: {len(valid_records)} | Invalid: {len(invalid_records)}"
    )

    return (valid_records, invalid_records)
