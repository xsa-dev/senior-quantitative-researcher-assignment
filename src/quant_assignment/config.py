from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PathsConfig:
    data_dir: Path = Path("documents")
    output_dir: Path = Path("outputs")

    @property
    def csv_dir(self) -> Path:
        return self.output_dir / "csv"
