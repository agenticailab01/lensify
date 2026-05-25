"""scikit-learn adapter — surfaces estimators, pipelines, splits, search.

Triggers on `sklearn` imports. Extracts:

    - Estimator instantiations (LogisticRegression, RandomForestClassifier,
      KMeans, SVC, GradientBoosting*, MLPClassifier, …) — broad regex
      catching CamelCase-ending names commonly used as estimators
    - Pipeline / make_pipeline constructions
    - train_test_split usage
    - GridSearchCV / RandomizedSearchCV / cross_val_score

Output: ## SKLEARN capsule section.
"""
from __future__ import annotations

import re

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from .._util import iter_python_with, truncate, line_of
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_HIGH, cap_entries,
    )
    from _util import iter_python_with, truncate, line_of  # type: ignore[no-redef]


# Common sklearn estimator class endings. Conservative whitelist to avoid
# matching e.g. user dataclasses.
_ESTIMATOR_NAMES = (
    r"LogisticRegression|LinearRegression|Ridge|Lasso|ElasticNet|"
    r"RandomForestClassifier|RandomForestRegressor|GradientBoostingClassifier|"
    r"GradientBoostingRegressor|HistGradientBoostingClassifier|"
    r"HistGradientBoostingRegressor|XGBClassifier|XGBRegressor|"
    r"DecisionTreeClassifier|DecisionTreeRegressor|ExtraTreesClassifier|"
    r"ExtraTreesRegressor|SVC|SVR|LinearSVC|KNeighborsClassifier|"
    r"KNeighborsRegressor|MLPClassifier|MLPRegressor|GaussianNB|"
    r"MultinomialNB|BernoulliNB|KMeans|DBSCAN|AgglomerativeClustering|"
    r"PCA|TruncatedSVD|StandardScaler|MinMaxScaler|RobustScaler|"
    r"OneHotEncoder|LabelEncoder|CountVectorizer|TfidfVectorizer|"
    r"ColumnTransformer"
)
_ESTIMATOR_RE = re.compile(
    rf"""(\w+)\s*=\s*(?:sklearn\.\w+\.)?({_ESTIMATOR_NAMES})\s*\("""
)
_PIPELINE_RE = re.compile(
    r"""(\w+)\s*=\s*(make_pipeline|Pipeline)\s*\("""
)
_SPLIT_RE = re.compile(
    r"""train_test_split\s*\("""
)
_SEARCH_RE = re.compile(
    r"""(\w+)\s*=\s*(GridSearchCV|RandomizedSearchCV|HalvingGridSearchCV|"""
    r"""HalvingRandomSearchCV)\s*\("""
)
_CV_RE = re.compile(r"""\b(cross_val_score|cross_validate)\s*\(""")


class SklearnAdapter(FrameworkAdapter):
    name = "sklearn"
    detect_signatures = ("import sklearn", "from sklearn")
    priority = PRIORITY_HIGH
    max_entries = 25

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["sklearn"]

        entries: list[FrameworkEntry] = []
        split_files: set[str] = set()
        cv_calls: set[tuple[str, str]] = set()

        for rel_path, text in iter_python_with(parsed_files, walk_result, "sklearn"):
            for m in _ESTIMATOR_RE.finditer(text):
                entries.append(_entry("estimator", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _PIPELINE_RE.finditer(text):
                entries.append(_entry("pipeline", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            for m in _SEARCH_RE.finditer(text):
                entries.append(_entry("search", m.group(1), m.group(2),
                                      rel_path, line_of(text, m.start())))
            if _SPLIT_RE.search(text):
                split_files.add(rel_path)
            for m in _CV_RE.finditer(text):
                cv_calls.add((m.group(1), rel_path))

        entries.sort(key=lambda e: (e.path, e.line))
        info.entries = cap_entries(entries, self.max_entries)
        info.meta["train_test_split_in"] = sorted(split_files)
        info.meta["cv_calls"] = sorted(cv_calls)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries and not info.meta.get("train_test_split_in"):
            return None
        lines = ["## SKLEARN"]
        for e in info.entries:
            lines.append(f"- {e.kind} `{e.name}` — {e.signature}  ({e.path}:{e.line})")
        splits = info.meta.get("train_test_split_in") or []
        if splits:
            lines.append(f"- train_test_split used in: {', '.join(splits[:5])}")
        cvs = info.meta.get("cv_calls") or []
        if cvs:
            fns = sorted({c[0] for c in cvs})
            lines.append(f"- cross-validation: {', '.join(fns)}")
        return truncate("\n".join(lines), budget_tokens)


def _entry(kind: str, name: str, cls: str, rel_path: str, line: int) -> FrameworkEntry:
    return FrameworkEntry(
        kind=kind, name=name, signature=cls,
        path=rel_path, line=line, confidence="EXTRACTED",
        meta={"class": cls},
    )
