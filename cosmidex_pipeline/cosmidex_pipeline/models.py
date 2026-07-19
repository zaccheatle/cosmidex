import logging
import typing
from dataclasses import dataclass, field, fields
from typing import Any, Optional, TypeVar, get_type_hints

import numpy as np
import pandas as pd

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


@dataclass
class ExoplanetRecord:
    pl_name: str = field(metadata={"pk": True})
    hostname: str = field(metadata={"pk": True})
    disc_year: Optional[int] = None
    discoverymethod: Optional[str] = None
    sy_dist: Optional[float] = None
    pl_rade: Optional[float] = None
    pl_bmasse: Optional[float] = None
    pl_dens: Optional[float] = None
    pl_orbeccen: Optional[float] = None
    pl_orbsmax: Optional[float] = None
    pl_orbper: Optional[float] = None
    pl_insol: Optional[float] = None
    pl_eqt: Optional[float] = None
    st_teff: Optional[float] = None
    st_lum: Optional[float] = None
    st_mass: Optional[float] = None
    st_rad: Optional[float] = None
    st_age: Optional[float] = None
    st_logg: Optional[float] = None
    st_met: Optional[float] = None


# Bind typevar to DataClassInstance so pylance knows the input is guaranteed to be a valid dataclass
T = TypeVar("T", bound=Any)


def get_base_type(hint):
    none_type = type(None)
    args = typing.get_args(hint)
    base = next((a for a in args if a is not none_type), hint)
    # treat numpy float/int as Python float/int
    if base is float:
        return (float, np.floating)
    if base is int:
        return (int, np.integer)
    return base


def parse_row(row: dict, data_class: type[T]) -> T:
    """
    Parse a dataframe row and validate it against the appropriate dataclass.

    Args:
        row (dict): Dataframe row.
        data_class (type[T]): The generic dataclass schema.

    Returns:
        T: Appropriate Dataclass object.

    Raises:
        ValueError: If primary key columns are blank or missing entirely.
        TypeError: If a field value doesn't match its dataclass type definition.
        KeyError: If a required column is completely missing from the row.
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

    logging.info(
        "Primary key columns present and populated, proceeding to schema validation..."
    )

    # 3. Check remaining fields for presence and correct data type
    for f in fields(data_class):
        # Ensure the column exists in the row
        if f.name not in row:
            logging.error(
                f"Required column '{f.name}' is completely missing from the data row."
            )
            raise KeyError(f"Missing expected column: '{f.name}'")

        value = row[f.name]

        # Verify the data type (skipping empty fields to allow for optional values)
        actual_types = get_type_hints(data_class)
        expected_type = actual_types[f.name]
        base_type = get_base_type(expected_type)
        if not pd.isna(value) and not isinstance(value, base_type):
            logging.error(
                f"Type Mismatch on '{f.name}': Expected {base_type}, got {type(value).__name__}."
            )
            raise TypeError(f"Column '{f.name}' requires type {base_type}.")

    expected_fields = {f.name for f in fields(data_class)}
    filtered_row = {k: v for k, v in row.items() if k in expected_fields}
    return data_class(**filtered_row)


def validate_records(
    df: pd.DataFrame, data_class: type[T]
) -> tuple[list[T], list[dict], list[str]]:
    """
    Validate dataframe records against the corresponding dataclass.

    Args:
        Dataframe (pd.DataFrame): Pandas dataframe with raw source data.
        data_class (DataClassInstance): Dataclass object.

    Returns:
        Tuple (list[t], list[dict]): Lists of valid and invalid record dicts.

    Raises:
        ValueError: If
        TypeError: If
        KeyError: If

    """

    expected_fields = {f.name for f in fields(data_class)}
    new_fields = set(df.columns) - expected_fields
    new_field_count = len(new_fields)

    if new_field_count > 0:
        logging.warning(
            f"ALERT!! {new_field_count} new fields detected! Dataclass requires an update!"
        )
    else:
        logging.info("0 new fields detected, proceeding...")

    row_dictionaries = df.to_dict(orient="records")

    valid_records = []
    invalid_records = []

    for row in row_dictionaries:
        try:
            obj = parse_row(row, data_class)
            valid_records.append(obj)
        except (ValueError, TypeError, KeyError) as e:
            logging.warning(f"Row validation failed: {e}")
            row_with_error = row.copy()
            row_with_error["__validation_error__"] = str(e)
            invalid_records.append(row_with_error)

    if new_field_count > 0:
        logging.warning(
            f"{new_field_count} new fields detected and added to return. Investigate and update dataclass."
        )
        return (valid_records, invalid_records, list(new_fields))
    else:
        return (valid_records, invalid_records, [])
