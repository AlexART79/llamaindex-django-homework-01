import csv
from pathlib import Path
from typing import Optional, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cvs.models import JobTitle, CV

REQUIRED_HEADERS = {
    "Name",
    "Job Title",
    "Years of Experience",
    "Skills",
    "Education",
    "Past experience",
}

def to_required_int(value: Optional[str], row_idx: int, field_label: str) -> int:
    s = "" if value is None else str(value).strip()
    if not s:
        raise CommandError(f"Row {row_idx}: '{field_label}' is required.")
    try:
        # Accept "5" or "5.0"
        return int(float(s))
    except ValueError as e:
        raise CommandError(
            f"Row {row_idx}: Invalid integer for '{field_label}': {value!r}"
        ) from e

class Command(BaseCommand):
    help = "Import candidate CSV into JobTitle and CV tables."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to input CSV file")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="How many CV rows to bulk-insert per batch (default: 500)",
        )
        parser.add_argument(
            "--encoding",
            type=str,
            default="utf-8-sig",
            help="CSV encoding (default: utf-8-sig; works with Excel exports)",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        csv_path = Path(opts["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        batch_size = opts["batch_size"]
        encoding = opts["encoding"]

        # Cache existing JobTitle rows by lowercased name to avoid duplicates in this run
        jobtitle_cache: Dict[str, JobTitle] = {
            jt.name.lower(): jt for jt in JobTitle.objects.all().only("id", "name")
        }

        def get_or_create_jobtitle(raw_title: str, row_idx: int) -> JobTitle:
            title = (raw_title or "").strip()
            if not title:
                raise CommandError(f"Row {row_idx}: 'Job Title' is required.")
            key = title.lower()

            jt = jobtitle_cache.get(key)
            if jt is not None:
                return jt

            # If DB already has a case-insensitive match but wasn't in cache (unlikely), reuse it
            jt = JobTitle.objects.filter(name__iexact=title).only("id", "name").first()
            if jt is None:
                jt = JobTitle.objects.create(name=title)
            jobtitle_cache[key] = jt
            return jt

        inserted_total = 0
        buffer: list[CV] = []

        with csv_path.open("r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV has no headers.")
            missing = REQUIRED_HEADERS - set(reader.fieldnames)
            if missing:
                raise CommandError(
                    f"CSV missing required columns: {sorted(missing)}\n"
                    f"Expected exactly: {sorted(REQUIRED_HEADERS)}"
                )

            for row_idx, row in enumerate(reader, start=2):  # header is row 1
                name = (row.get("Name") or "").strip()
                if not name:
                    # Skip rows without a Name (treat as blank)
                    continue

                job_title = get_or_create_jobtitle(row.get("Job Title"), row_idx)
                years = to_required_int(row.get("Years of Experience"), row_idx, "Years of Experience")
                skills = (row.get("Skills") or "").strip()
                education = (row.get("Education") or "").strip()
                past_experience = (row.get("Past experience") or "").strip()

                buffer.append(
                    CV(
                        name=name,
                        job_title=job_title,
                        years_of_experience=years,
                        skills=skills,
                        education=education,
                        past_experience=past_experience,
                    )
                )

                if len(buffer) >= batch_size:
                    CV.objects.bulk_create(buffer, ignore_conflicts=False)
                    inserted_total += len(buffer)
                    buffer.clear()

        if buffer:
            CV.objects.bulk_create(buffer, ignore_conflicts=False)
            inserted_total += len(buffer)

        self.stdout.write(self.style.SUCCESS(f"Imported {inserted_total} CVs."))
