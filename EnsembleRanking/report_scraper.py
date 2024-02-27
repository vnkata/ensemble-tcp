import pathlib
from distutils.version import StrictVersion

def scrape_xml_reports(reports_path):
    reports = []
    reports_dir = pathlib.Path(reports_path)
    for report_file in reports_dir.rglob('*.xml'):
        reports.append(str(report_file.resolve()))
    reports.sort()
    return reports


def scrape_reports(reports_path):
    reports = []
    reports_dir = pathlib.Path(reports_path)
    for report_file in reports_dir.rglob('*.csv'):
        reports.append(str(report_file.resolve()))

    reports.sort()
    return reports


def scrape_json_reports(reports_path):
    releases = []
    reports_dir = pathlib.Path(reports_path)
    for report_file in reports_dir.rglob('*.json'):
        releases.append(report_file.stem.replace('_', '.'))

    releases.sort(key=StrictVersion)
    return [str((reports_dir / (release.replace('.', '_') + '.json')).resolve()) for release in releases]
