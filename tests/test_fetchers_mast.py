from __future__ import annotations

from astropy.table import Table

from server.fetchers import mast


class _FakeObservations:
    last_query_args: dict[str, object] | None = None
    last_product_request: object | None = None

    @classmethod
    def query_region(cls, coord, radius):  # type: ignore[override]
        cls.last_query_args = {"coord": coord, "radius": radius}
        table = Table()
        table["obsid"] = [123, 999]
        table["obs_id"] = ["OBS123", "OBS999"]
        table["dataproduct_type"] = ["spectrum", "image"]
        table["obs_title"] = ["Test spectrum", "Other"]
        table["target_name"] = ["Target A", "Target B"]
        table["s_ra"] = [10.0, 11.0]
        table["s_dec"] = [20.0, 21.0]
        table["em_min"] = [1.0e-7, 1.0e-7]
        table["em_max"] = [2.0e-7, 2.0e-7]
        table["s_resolution"] = [1200.0, 0.0]
        table["obs_collection"] = ["HST", "HST"]
        table["provenance_name"] = ["CALSPEC v1", "IMAGE"]
        table["flux_units"] = ["erg/s/cm^2/Å", "erg/s/cm^2/Å"]
        table["data_doi"] = ["10.17909/T9XX11", ""]
        table["dataURL"] = [
            "https://mast.stsci.edu/spectrum.fits",
            "https://mast.stsci.edu/image.fits",
        ]
        table["jpegURL"] = [
            "https://mast.stsci.edu/spectrum.jpg",
            "https://mast.stsci.edu/image.jpg",
        ]
        table["instrument_name"] = ["STIS", "WFC3"]
        table["filters"] = ["G140L", "F606W"]
        table["proposal_id"] = ["12345", "54321"]
        table["proposal_pi"] = ["Doe", "Roe"]
        table["t_exptime"] = [1500.0, 400.0]
        table["dataRights"] = ["PUBLIC", "PUBLIC"]
        return table

    @classmethod
    def get_product_list(cls, obsid):  # type: ignore[override]
        cls.last_product_request = obsid
        table = Table()
        table["dataproduct_type"] = ["spectrum", "spectrum"]
        table["productType"] = ["SCIENCE", "PREVIEW"]
        table["dataURI"] = [
            "mast:HLSP/test/spectrum.fits",
            "mast:HLSP/test/preview.jpg",
        ]
        table["description"] = ["Calibrated spectrum", "Preview"]
        return table


def test_mast_search_products(monkeypatch) -> None:
    monkeypatch.setattr(mast, "Observations", _FakeObservations)

    hits = list(mast.search_products(ra=10.0, dec=20.0, radius_arcsec=5.0))

    assert len(hits) == 1
    hit = hits[0]
    product = hit.product
    assert hit.provider == "MAST"
    assert hit.preview_url == "https://mast.stsci.edu/spectrum.jpg"
    assert product.provider == "MAST"
    assert product.product_id == "123"
    assert product.title == "Test spectrum"
    assert product.target == "Target A"
    assert product.ra == 10.0
    assert product.dec == 20.0
    assert product.wave_range_nm == (100.0, 200.0)
    assert product.resolution_R == 1200.0
    assert product.pipeline_version == "CALSPEC v1"
    assert product.urls["product"] == "https://mast.stsci.edu/spectrum.fits"
    assert product.urls["download"].startswith("https://mast.stsci.edu/api/v0.1/Download/file?uri=")
    assert product.doi == "10.17909/T9XX11"
    assert product.extra["filters"] == "G140L"
    assert _FakeObservations.last_product_request == 123
