"""Great Expectations validation suite for production data."""
from dataclasses import dataclass

import great_expectations as gx
import pandas as pd


@dataclass
class ValidationResult:
    success: bool
    failed_expectations: list[str]
    n_rows: int


def validate_production_df(df: pd.DataFrame) -> ValidationResult:
    """Run a fixed set of expectations against the production dataframe."""
    if df.empty:
        return ValidationResult(success=False, failed_expectations=["empty_df"], n_rows=0)

    context = gx.get_context(mode="ephemeral")
    asset = context.data_sources.add_pandas("prod").add_dataframe_asset("daily")
    batch = asset.add_batch_definition_whole_dataframe("batch").get_batch(
        batch_parameters={"dataframe": df}
    )

    suite = context.suites.add(gx.ExpectationSuite(name="production_v3"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="Date"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
        column="Production journaliere d'huile bbl", min_value=0, max_value=200000,
        mostly=0.99,
    ))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
        column="Teneur en eau (Watercut)", min_value=0, max_value=100, mostly=0.99,
    ))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
        column="Nombre des puits actifs", min_value=0, max_value=200,
    ))

    result = batch.validate(suite)
    failed = [
        r["expectation_config"]["type"]
        for r in result["results"] if not r["success"]
    ]
    return ValidationResult(
        success=result["success"],
        failed_expectations=failed,
        n_rows=len(df),
    )
