import pytest

from abtest.simulation import exaggerated_winners, peeking
from abtest.stats import compare, sample_size


def test_sample_size_matches_the_textbook_example():
    # 10% -> 12% at 5% significance and 80% power is the classic ~3,840 per group.
    assert 3800 <= sample_size(0.10, 0.20) <= 3900


def test_smaller_lifts_need_many_more_visitors():
    assert sample_size(0.03, 0.05) > 3.5 * sample_size(0.03, 0.10)


def test_sample_size_rejects_impossible_inputs():
    with pytest.raises(ValueError):
        sample_size(0, 0.1)
    with pytest.raises(ValueError):
        sample_size(0.6, 1.0)


def test_compare_matches_a_hand_calculation():
    # 100/1000 vs 130/1000: z = 0.03 / 0.014267 = 2.103, two-sided p = 0.0355
    result = compare(100, 1000, 130, 1000)
    assert result["p_value"] == pytest.approx(0.0355, abs=0.0005)
    assert result["significant"]
    assert result["relative_lift"] == pytest.approx(0.30)
    assert result["difference_low"] > 0


def test_identical_results_are_not_significant():
    result = compare(50, 1000, 50, 1000)
    assert result["p_value"] == pytest.approx(1.0)
    assert not result["significant"]


def test_looking_once_keeps_false_alarms_near_five_percent():
    report = peeking(simulations=20000).set_index("schedule")["false_alarm_pct"]
    assert 4.0 <= report["Solo al final"] <= 6.0
    assert report["Cada día"] > report["Cada semana"] > report["Solo al final"]


def test_underpowered_winners_exaggerate_and_full_tests_reach_planned_power():
    report = exaggerated_winners(simulations=100000).set_index("share_of_needed_visitors_pct")
    assert 77 <= report.loc[100, "tests_that_detect_it_pct"] <= 83   # planned power: 80%
    assert report.loc[10, "lift_reported_by_winners_pct"] > 2 * report.loc[10, "true_lift_pct"]
    assert (report["lift_reported_by_winners_pct"].diff().dropna() < 0).all()
