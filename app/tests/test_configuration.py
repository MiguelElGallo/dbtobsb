"""Resource-binding validation tests."""

import pytest

from dbtobsb_app.configuration import (
    COLLECTION_HEALTH_VIEW_ENV,
    NODE_HEALTH_VIEW_ENV,
    REQUIRED_BINDINGS,
    RUN_HEALTH_VIEW_ENV,
    WAREHOUSE_ID_ENV,
    BindingState,
    resolve_bindings,
)


def _environment(**overrides: str) -> dict[str, str]:
    values = {
        WAREHOUSE_ID_ENV: "0123456789abcdef",
        RUN_HEALTH_VIEW_ENV: "customer-catalog.dbt_obs.dbt_run_health",
        NODE_HEALTH_VIEW_ENV: "customer-catalog.dbt_obs.dbt_node_health",
        COLLECTION_HEALTH_VIEW_ENV: "customer-catalog.dbt_obs.dbt_collection_health",
    }
    values.update(overrides)
    return values


def test_absent_bindings_are_setup_only() -> None:
    bindings = resolve_bindings({})

    assert bindings.state is BindingState.SETUP_REQUIRED
    assert bindings.missing == REQUIRED_BINDINGS
    assert bindings.warehouse_id is None


def test_partial_bindings_name_only_the_missing_resource() -> None:
    bindings = resolve_bindings({WAREHOUSE_ID_ENV: "0123456789abcdef"})

    assert bindings.state is BindingState.SETUP_REQUIRED
    assert bindings.missing == (
        RUN_HEALTH_VIEW_ENV,
        NODE_HEALTH_VIEW_ENV,
        COLLECTION_HEALTH_VIEW_ENV,
    )


def test_ready_bindings_preserve_and_quote_literal_names() -> None:
    bindings = resolve_bindings(_environment())

    assert bindings.ready
    assert bindings.run_health_view is not None
    assert bindings.run_health_view.quoted == "`customer-catalog`.`dbt_obs`.`dbt_run_health`"
    assert bindings.node_health_view is not None
    assert bindings.node_health_view.quoted == "`customer-catalog`.`dbt_obs`.`dbt_node_health`"
    assert bindings.collection_health_view is not None
    assert bindings.collection_health_view.quoted == (
        "`customer-catalog`.`dbt_obs`.`dbt_collection_health`"
    )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (WAREHOUSE_ID_ENV, "not-a-warehouse"),
        (WAREHOUSE_ID_ENV, "A123456789abcdef"),
        (RUN_HEALTH_VIEW_ENV, "catalog.schema.other_view"),
        (RUN_HEALTH_VIEW_ENV, "catalog.schema.dbt_run_health.extra"),
        (RUN_HEALTH_VIEW_ENV, "catalog.schema.`dbt_run_health`"),
        (RUN_HEALTH_VIEW_ENV, "catalog.schema.dbt run health"),
        (NODE_HEALTH_VIEW_ENV, "catalog.schema.other_view"),
        (COLLECTION_HEALTH_VIEW_ENV, "catalog.schema.other_view"),
    ],
)
def test_untrusted_binding_shapes_fail_closed(name: str, value: str) -> None:
    bindings = resolve_bindings(_environment(**{name: value}))

    assert bindings.state is BindingState.INVALID
    assert bindings.warehouse_id is None
    assert bindings.run_health_view is None
    assert bindings.node_health_view is None
    assert bindings.collection_health_view is None


def test_views_must_share_the_exact_catalog_and_schema() -> None:
    bindings = resolve_bindings(
        _environment(**{NODE_HEALTH_VIEW_ENV: "other.dbt_obs.dbt_node_health"})
    )

    assert bindings.state is BindingState.INVALID
