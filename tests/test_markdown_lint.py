#!/usr/bin/env python3
"""
Unit tests for support_python.markdown.lint.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support_python.markdown import lint as lint_markdown

MarkdownLinter = lint_markdown.MarkdownLinter
LintIssue = lint_markdown.LintIssue


class TestRuleMD001HeadingIncrement(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_valid_heading_hierarchy_passes(self) -> None:
        content = b"# Title\n\n## Section\n\n### Subsection\n\n## Next Section\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md001 = [i for i in issues if i.rule_id == "MD001"]
        self.assertEqual(md001, [])

    def test_skipped_heading_level_flags_md001(self) -> None:
        content = b"# Title\n\n### Skipped to H3\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md001 = [i for i in issues if i.rule_id == "MD001"]
        self.assertEqual(len(md001), 1)
        self.assertEqual(md001[0].line_number, 3)
        self.assertIn("skipped from H1 to H3", md001[0].message)

    def test_heading_in_code_block_ignored(self) -> None:
        content = b"# Title\n\n```python\n### Not a heading\n```\n\n## Section\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md001 = [i for i in issues if i.rule_id == "MD001"]
        self.assertEqual(md001, [])


class TestRuleMD002SingleH1(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_single_h1_passes(self) -> None:
        content = b"# Main Title\n\n## Section 1\n\n## Section 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md002 = [i for i in issues if i.rule_id == "MD002"]
        self.assertEqual(md002, [])

    def test_multiple_h1_flags_md002(self) -> None:
        content = b"# First H1\n\n## Sub\n\n# Second H1\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md002 = [i for i in issues if i.rule_id == "MD002"]
        self.assertEqual(len(md002), 1)
        self.assertEqual(md002[0].line_number, 5)
        self.assertIn("Multiple H1 headings found", md002[0].message)


class TestRuleMD003NoNumberedHeadings(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_un开展numbered_headings_pass(self) -> None:
        content = b"# Title\n\n## Introduction\n\n### Background Context\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md003 = [i for i in issues if i.rule_id == "MD003"]
        self.assertEqual(md003, [])

    def test_numbered_headings_flag_md003(self) -> None:
        content = b"# Title\n\n## 1. Introduction\n\n### 1.1 Details\n\n## 2 - Summary\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md003 = [i for i in issues if i.rule_id == "MD003"]
        self.assertEqual(len(md003), 3)
        self.assertEqual(md003[0].line_number, 3)
        self.assertEqual(md003[1].line_number, 5)
        self.assertEqual(md003[2].line_number, 7)


class TestRuleMD004NoBoldHeading(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_valid_bolding_passes(self) -> None:
        content = b"# Title\n\nParagraph with **bold text** inside.\n\n- **Term:** Definition of term.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md004 = [i for i in issues if i.rule_id == "MD004"]
        self.assertEqual(md004, [])

    def test_standalone_bold_heading_flags_md004(self) -> None:
        content = b"# Title\n\n**Section Header:**\n\nSome paragraph text.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md004 = [i for i in issues if i.rule_id == "MD004"]
        self.assertEqual(len(md004), 1)
        self.assertEqual(md004[0].line_number, 3)

    def test_blockquote_lead_in_not_flagged(self) -> None:
        content = b"# Title\n\n> **Note:**\n> Explanatory note inside blockquote.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md004 = [i for i in issues if i.rule_id == "MD004"]
        self.assertEqual(md004, [])


class TestRuleMD005DashBullets(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_dash_bullets_pass(self) -> None:
        content = b"# Title\n\n- First item\n- Second item\n  - Sub item\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md005 = [i for i in issues if i.rule_id == "MD005"]
        self.assertEqual(md005, [])

    def test_asterisk_and_plus_bullets_flag_md005(self) -> None:
        content = b"# Title\n\n* Asterisk item\n+ Plus item\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md005 = [i for i in issues if i.rule_id == "MD005"]
        self.assertEqual(len(md005), 2)
        self.assertTrue(md005[0].fixable)
        self.assertTrue(md005[1].fixable)


class TestRuleMD006NoFullyBoldBullet(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_glossary_bullet_passes(self) -> None:
        content = b"# Glossary\n\n- **Term:** Definition of the term.\n- **Another Term:** Another description.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md006 = [i for i in issues if i.rule_id == "MD006"]
        self.assertEqual(md006, [])

    def test_fully_bolded_bullet_flags_md006(self) -> None:
        content = b"# Rules\n\n- **This entire sentence is bolded for emphasis.**\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md006 = [i for i in issues if i.rule_id == "MD006"]
        self.assertEqual(len(md006), 1)
        self.assertEqual(md006[0].line_number, 3)


class TestRuleMD007CodeBlockLanguage(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_annotated_code_block_passes(self) -> None:
        content = b"# Code\n\n```python\nprint('hello')\n```\n\n```bash\ngit status\n```\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md007 = [i for i in issues if i.rule_id == "MD007"]
        self.assertEqual(md007, [])

    def test_unannotated_code_block_flags_md007(self) -> None:
        content = b"# Code\n\n```\nplain text\n```\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md007 = [i for i in issues if i.rule_id == "MD007"]
        self.assertEqual(len(md007), 1)
        self.assertEqual(md007[0].line_number, 3)


class TestRuleMD008NoRawUrls(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_formatted_urls_pass(self) -> None:
        content = (
            b"# Links\n\n"
            b"- Inline: [Example](https://example.com)\n"
            b"- Autolink: <https://example.com>\n"
            b"- Code: `https://example.com`\n"
            b"- Ref link: [Source]\n\n"
            b"[Source]: https://example.com\n"
        )
        issues = self.linter.lint_content(Path("test.md"), content)
        md008 = [i for i in issues if i.rule_id == "MD008"]
        self.assertEqual(md008, [])

    def test_bare_url_flags_md008(self) -> None:
        content = b"# Links\n\nVisit https://example.com for more info.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md008 = [i for i in issues if i.rule_id == "MD008"]
        self.assertEqual(len(md008), 1)
        self.assertEqual(md008[0].line_number, 3)


class TestRuleMD009NoFileUri(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_relative_links_pass(self) -> None:
        content = b"# Links\n\nSee [DevOps Guide](docs/devops.md) for instructions.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md009 = [i for i in issues if i.rule_id == "MD009"]
        self.assertEqual(md009, [])

    def test_file_uri_flags_md009(self) -> None:
        content = b"# Links\n\nSee [DevOps](file:///c:/Dev-Projects/dev-guidelines/docs/devops.md).\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md009 = [i for i in issues if i.rule_id == "MD009"]
        self.assertEqual(len(md009), 1)
        self.assertEqual(md009[0].line_number, 3)


class TestRuleMD010NoTabs(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_spaces_pass(self) -> None:
        content = b"# Title\n\n    Four spaces indent\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md010 = [i for i in issues if i.rule_id == "MD010"]
        self.assertEqual(md010, [])

    def test_tabs_flag_md010(self) -> None:
        content = b"# Title\n\n\tTab indented line\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md010 = [i for i in issues if i.rule_id == "MD010"]
        self.assertEqual(len(md010), 1)
        self.assertTrue(md010[0].fixable)


class TestRuleMD011TrailingWhitespace(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_clean_lines_pass(self) -> None:
        content = b"# Title\n\nClean line without trailing spaces.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md011 = [i for i in issues if i.rule_id == "MD011"]
        self.assertEqual(md011, [])

    def md011(self, content: bytes) -> list:
        return [i for i in self.linter.lint_content(Path("test.md"), content) if i.rule_id == "MD011"]

    def test_one_and_two_trailing_spaces_pass(self) -> None:
        self.assertEqual(self.md011(b"# Title\n\nLine with one space. \n"), [])
        self.assertEqual(self.md011(b"# Title\n\nHard break line.  \nNext line.\n"), [])

    def test_three_spaces_or_tabs_flag_md011(self) -> None:
        for line in (b"Three spaces.   ", b"Tab.\t", b"Space then tab. \t", b"Tab then space.\t "):
            issues = self.md011(b"# Title\n\n" + line + b"\n")
            self.assertEqual(len(issues), 1, line)
            self.assertTrue(issues[0].fixable)
            self.assertIn("two", issues[0].message)

    def test_fix_trims_long_runs_to_two_spaces_and_removes_tabs(self) -> None:
        content = b"# Title\n\nFour.    \nTab.\t\nMixed. \t \nTwo.  \nOne. \n"
        fixed = self.linter.fix_content(Path("test.md"), content)
        self.assertEqual(fixed, b"# Title\n\nFour.  \nTab.\nMixed.\nTwo.  \nOne. \n")


class TestRuleMD012MixedLineEndings(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_consistent_lf_passes(self) -> None:
        content = b"# Title\n\nLine 1\nLine 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md012 = [i for i in issues if i.rule_id == "MD012"]
        self.assertEqual(md012, [])

    def test_mixed_line_endings_flag_md012(self) -> None:
        content = b"# Title\r\n\nLine 1\r\nLine 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md012 = [i for i in issues if i.rule_id == "MD012"]
        self.assertEqual(len(md012), 1)
        self.assertTrue(md012[0].fixable)


class TestRuleMD013NoTaskIdsInChangelog(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_clean_changelog_passes(self) -> None:
        content = (
            b"# Versioned Changes\n\n"
            b"## v1.0.0 [2026-09-01]\n"
            b"- CLI: Added version subcommand and help documentation\n"
            b"- DevEx: Improved test suite coverage for configuration loading\n"
        )
        issues = self.linter.lint_content(Path("CHANGELOG.md"), content)
        md013 = [i for i in issues if i.rule_id == "MD013"]
        self.assertEqual(md013, [])

    def test_task_id_in_changelog_flags_md013(self) -> None:
        content = (
            b"# Versioned Changes\n\n"
            b"## v1.0.0 [2026-09-01]\n"
            b"- CLI: Added version command (T0091)\n"
            b"- DevEx: Fixed setup script A0012 for Windows\n"
            b"- Docs: Updated guide per [T0031](./tasks/T0031.md)\n"
        )
        issues = self.linter.lint_content(Path("CHANGELOG.md"), content)
        md013 = [i for i in issues if i.rule_id == "MD013"]
        self.assertEqual(len(md013), 3)
        self.assertEqual(md013[0].line_number, 4)
        self.assertEqual(md013[1].line_number, 5)
        self.assertEqual(md013[2].line_number, 6)
        self.assertIn("T0091", md013[0].message)
        self.assertIn("A0012", md013[1].message)
        self.assertIn("T0031", md013[2].message)

    def test_task_id_in_non_changelog_file_ignored(self) -> None:
        content = b"# TODO\n\n- [~] T0091 [owner: @gemini] Working on task\n- [ ] A0012 Adhoc task\n"
        issues = self.linter.lint_content(Path("TODO.md"), content)
        md013 = [i for i in issues if i.rule_id == "MD013"]
        self.assertEqual(md013, [])


class TestRuleMD014ValidRelativeLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_valid_relative_link_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "existing.md"
            target_file.write_text("# Existing\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Existing](existing.md) for details.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_nonexistent_relative_link_flags_md014(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Missing](missing-file.md) for details.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertEqual(md014[0].line_number, 3)
            self.assertIn("missing-file.md", md014[0].message)

    def test_external_urls_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = (
                b"# Document\n\n"
                b"- [Web](https://example.com/docs)\n"
                b"- [Insecure](http://example.com)\n"
                b"- [Email](mailto:user@example.com)\n"
                b"- [FTP](ftp://example.com/file.txt)\n"
            )
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_valid_intra_document_anchor_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = b"# Document\n\n## My Section\n\nSee [Section](#my-section) below.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_invalid_intra_document_anchor_flags_md014(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Section](#my-section) below.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertEqual(md014[0].line_number, 3)
            self.assertIn("#my-section", md014[0].message)

    def test_relative_link_with_anchor_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "guide.md"
            target_file.write_text("# Guide\n\n## Section\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Guide Section](guide.md#section) for info.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_relative_image_link_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            img_file = base / "screenshot.png"
            img_file.write_bytes(b"fake png")
            doc_file = base / "doc.md"
            content = b"# Document\n\n![Valid Image](screenshot.png)\n![Missing Image](missing.png)\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertEqual(md014[0].line_number, 4)
            self.assertIn("missing.png", md014[0].message)

    def test_reference_definition_link_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "ref-target.md"
            target_file.write_text("# Target\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = (
                b"# Document\n\n"
                b"See [Target Reference][target] and [Missing Ref][missing].\n\n"
                b"[target]: ref-target.md\n"
                b"[missing]: missing-target.md\n"
            )
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertEqual(md014[0].line_number, 6)
            self.assertIn("missing-target.md", md014[0].message)

    def test_code_span_containing_link_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = b"# Document\n\nCode snippet: `[fake](nonexistent.md)` inside prose.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_link_with_code_span_in_text_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [`MyClass`](nonexistent.py) for details.\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertEqual(md014[0].line_number, 3)
            self.assertIn("nonexistent.py", md014[0].message)

    def test_url_encoded_relative_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "file with spaces.md"
            target_file.write_text("# Spaces\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Spaced File](file%20with%20spaces.md).\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_angle_bracket_relative_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "guide.md"
            target_file.write_text("# Guide\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = b"# Document\n\nSee [Guide](<guide.md>).\n"
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])

    def test_link_with_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target_file = base / "guide.md"
            target_file.write_text("# Guide\n", encoding="utf-8")
            doc_file = base / "doc.md"
            content = b'# Document\n\nSee [Guide](guide.md "User Guide").\n'
            issues = self.linter.lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(md014, [])


class TestRuleMD015NoBlankLineAfterSubheading(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_subheading_without_blank_line_passes(self) -> None:
        content = b"# Title\n\n## Section\nContent directly follows.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])

    def test_h1_with_blank_line_allowed(self) -> None:
        content = b"# Title\n\n## Section\nContent directly follows.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])

    def test_subheading_with_blank_line_flags_md015(self) -> None:
        content = b"# Title\n\n## Section\n\nContent after blank line.\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(len(md015), 1)
        self.assertEqual(md015[0].line_number, 3)
        self.assertIn("must not be followed by a blank line", md015[0].message)

    def test_empty_subheading_followed_by_heading_with_blank_lines_passes(self) -> None:
        content = b"# Title\n\n## Section 1\n\n## Section 2\nContent\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])

    def test_empty_subheading_followed_by_subheading_with_blank_lines_passes(self) -> None:
        content = b"# Title\n\n## Major Section\n\n### Subsection\nContent\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])

    def test_empty_subheading_followed_by_hr_passes(self) -> None:
        content = b"# Title\n\n## Section 1\n\n---\n\n## Section 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])

    def test_subheading_in_code_block_ignored(self) -> None:
        content = b"# Title\n\n```markdown\n## Section in code\n\nContent\n```\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md015 = [i for i in issues if i.rule_id == "MD015"]
        self.assertEqual(md015, [])


class TestRuleMD016NoBlankLineBeforeList(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_intro_sentence_without_blank_line_passes(self) -> None:
        content = b"# Title\n\nIntroduction to items:\n- Item 1\n- Item 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md016 = [i for i in issues if i.rule_id == "MD016"]
        self.assertEqual(md016, [])

    def test_intro_sentence_with_blank_line_flags_md016(self) -> None:
        content = b"# Title\n\nIntroduction to items:\n\n- Item 1\n- Item 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md016 = [i for i in issues if i.rule_id == "MD016"]
        self.assertEqual(len(md016), 1)
        self.assertEqual(md016[0].line_number, 3)
        self.assertIn("Sentence introducing a list must not be followed by a blank line", md016[0].message)

    def test_sentence_not_ending_in_colon_not_flagged(self) -> None:
        content = b"# Title\n\nGeneral paragraph ending in period.\n\n- Item 1\n- Item 2\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md016 = [i for i in issues if i.rule_id == "MD016"]
        self.assertEqual(md016, [])


class TestRuleMD017AlignedTables(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_aligned_table_passes(self) -> None:
        content = (
            b"# Title\n\n"
            b"| ID  | Name    | Score |\n"
            b"| :-: | :------ | ----: |\n"
            b"|  1  | Alice   |   100 |\n"
            b"|  22 | Bob     |   9.5 |\n"
        )
        issues = self.linter.lint_content(Path("test.md"), content)
        md017 = [i for i in issues if i.rule_id == "MD017"]
        self.assertEqual(md017, [])

    def test_misaligned_table_flags_md017(self) -> None:
        content = b"# Title\n\n| Col A | Col B |\n|:-|---|\n| Value 1 | Short |\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md017 = [i for i in issues if i.rule_id == "MD017"]
        self.assertTrue(len(md017) > 0)
        self.assertEqual(md017[0].rule_id, "MD017")
        self.assertIn("vertically aligned", md017[0].message)

    def test_table_in_code_block_ignored(self) -> None:
        content = b"# Title\n\n```markdown\n| Col A | Col B |\n|:-|---|\n| 1 | 2 |\n```\n"
        issues = self.linter.lint_content(Path("test.md"), content)
        md017 = [i for i in issues if i.rule_id == "MD017"]
        self.assertEqual(md017, [])


class TestRuleMD018ValidExternalLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_valid_external_url_passes(self) -> None:
        content = b"# Links\n\nSee [Real](https://real-domain-service.org/docs).\n"
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = mock_open.return_value.__enter__.return_value
            mock_resp.status = 200
            issues = self.linter.lint_content(Path("test.md"), content)
            md018 = [i for i in issues if i.rule_id == "MD018"]
            self.assertEqual(md018, [])

    def test_invalid_external_url_flags_md018(self) -> None:
        import urllib.error

        content = b"# Links\n\nSee [Bad](https://broken-service-link.org/404).\n"
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError("https://broken-service-link.org/404", 404, "Not Found", {}, None)
            issues = self.linter.lint_content(Path("test.md"), content)
            md018 = [i for i in issues if i.rule_id == "MD018"]
            self.assertEqual(len(md018), 1)
            self.assertEqual(md018[0].line_number, 3)
            self.assertIn("failed validation", md018[0].message)

    def test_offline_mode_skips_external_validation(self) -> None:
        linter = MarkdownLinter(offline=True)
        content = b"# Links\n\nSee [Broken](https://unreachable-host-example.com/bad).\n"
        with patch("urllib.request.urlopen") as mock_open:
            issues = linter.lint_content(Path("test.md"), content)
            md018 = [i for i in issues if i.rule_id == "MD018"]
            self.assertEqual(md018, [])
            mock_open.assert_not_called()

    def test_local_dev_guidelines_github_url_resolves_locally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir).resolve()
            dev_guidelines = workspace / "dev-guidelines" / "scripts"
            dev_guidelines.mkdir(parents=True)
            (dev_guidelines / "generate-agent-digest.py").write_text("# script\n", encoding="utf-8")
            sibling_proj = workspace / "sibling-repo"
            (sibling_proj / ".git").mkdir(parents=True)

            content = (
                b"# Links\n\n"
                b"See [generate-agent-digest.py](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/generate-agent-digest.py).\n"
            )
            with patch("urllib.request.urlopen") as mock_open:
                issues = self.linter.lint_content(sibling_proj / "test.md", content)
                md018 = [i for i in issues if i.rule_id == "MD018"]
                self.assertEqual(md018, [])
                mock_open.assert_not_called()

                missing_content = (
                    b"# Links\n\nSee [missing.py](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/missing.py).\n"
                )
                missing_issues = self.linter.lint_content(sibling_proj / "test.md", missing_content)
                missing_md018 = [i for i in missing_issues if i.rule_id == "MD018"]
                self.assertEqual(len(missing_md018), 1)
                self.assertIn("does not exist on disk in 'dev-guidelines'", missing_md018[0].message)
                mock_open.assert_not_called()


class TestRuleMD019FileReferencesAsLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_proper_markdown_link_passes(self) -> None:
        content = b"# Guide\n\nSee [generate-agent-digest.py](../scripts/generate-agent-digest.py) for info.\n"
        issues = self.linter.lint_content(Path("guidelines/doc.md"), content)
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md019, [])

    def test_bare_file_path_in_prose_flags_md019(self) -> None:
        content = b"# Guide\n\nRun scripts/generate-agent-digest.py to stop processes.\n"
        issues = self.linter.lint_content(Path("doc.md"), content)
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(len(md019), 1)
        self.assertEqual(md019[0].line_number, 3)
        self.assertIn("Bare file path", md019[0].message)

    def test_bare_missing_file_path_asks_for_code_span(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            content = b"# Guide\n\nThe old src/support_python/backup.py module is gone.\n"
            issues = self.linter.lint_content(proj_root / "doc.md", content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(len(md019), 1)
            self.assertIn("code span", md019[0].message)

    def test_bare_existing_file_path_asks_for_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "src").mkdir()
            (proj_root / "src" / "app.py").write_text("# app\n", encoding="utf-8")
            content = b"# Guide\n\nRun src/app.py directly.\n"
            issues = self.linter.lint_content(proj_root / "doc.md", content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(len(md019), 1)
            self.assertIn("markdown link", md019[0].message)

    def test_backticked_missing_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            content = b"# Guide\n\nThe old `src/support_python/backup.py` module is gone.\n"
            issues = self.linter.lint_content(proj_root / "doc.md", content)
            self.assertEqual([i for i in issues if i.rule_id == "MD019"], [])

    def test_task_files_are_exempt_from_md019(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "src").mkdir()
            (proj_root / "src" / "app.py").write_text("# app\n", encoding="utf-8")
            task_dir = proj_root / ".plan" / "tasks"
            spec = task_dir / "T0200-active-task" / "technical-spec.md"
            spec.parent.mkdir(parents=True)
            task_content = b"---\nid: T0200\nstatus: ready\n---\n# T0200: Active\n\n## Goals\nChange src/app.py and `src/app.py`.\n"
            for path, content in ((task_dir / "T0200-active-task.md", task_content), (spec, b"### Declared Files\n- src/app.py\n")):
                for linter in (self.linter, MarkdownLinter(profile="default")):
                    issues = linter.lint_content(path, content)
                    self.assertEqual([i for i in issues if i.rule_id == "MD019"], [], f"{path.name} {linter.profile}")

    def test_backticked_repo_file_flags_md019(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "scripts").mkdir()
            (proj_root / "scripts" / "generate-agent-digest.py").write_text("# script\n", encoding="utf-8")
            content = b"# Guide\n\nUse `scripts/generate-agent-digest.py` script.\n"
            issues = self.linter.lint_content(proj_root / "doc.md", content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(len(md019), 1)
            self.assertEqual(md019[0].line_number, 3)
            self.assertIn("Repository file reference", md019[0].message)

    def test_generic_files_not_flagged(self) -> None:
        content = b"# Guide\n\nCheck `package.json` and `CHANGELOG.md`.\n"
        issues = self.linter.lint_content(Path("doc.md"), content)
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md019, [])

    def test_command_invocation_with_spaces_not_flagged(self) -> None:
        content = b"# Guide\n\nRun `python scripts/generate-agent-digest.py 123` in terminal.\n"
        issues = self.linter.lint_content(Path("doc.md"), content)
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md019, [])

    def test_anti_pattern_avoid_line_not_flagged(self) -> None:
        content = b"# Guide\n\nAvoid `scripts/lint-markdown.py`; use [lint-markdown.py](scripts/lint-markdown.py).\n"
        issues = self.linter.lint_content(Path("doc.md"), content)
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md019, [])

    def test_backticked_file_in_custom_project_root_flags_md019(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            src_dir = proj_root / "src"
            src_dir.mkdir(parents=True)
            custom_file = src_dir / "custom_module.py"
            custom_file.write_text("print('hello')", encoding="utf-8")

            doc_path = proj_root / "docs" / "guide.md"
            doc_path.parent.mkdir(parents=True)
            content = b"# Guide\n\nRefer to `src/custom_module.py` for API details.\n"

            linter = MarkdownLinter(project_root=proj_root)
            issues = linter.lint_content(doc_path, content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(len(md019), 1)
            self.assertIn("Repository file reference 'src/custom_module.py'", md019[0].message)

    def test_backticked_dev_guidelines_file_not_flagged_in_other_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            doc_path = proj_root / "docs" / "guide.md"
            doc_path.parent.mkdir(parents=True)
            content = b"# Guide\n\nUse `scripts/generate-agent-digest.py` script.\n"

            linter = MarkdownLinter(project_root=proj_root)
            issues = linter.lint_content(doc_path, content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(md019, [])

    def test_project_root_auto_discovered_from_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            src_dir = proj_root / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "app.py").write_text("# app", encoding="utf-8")

            doc_path = proj_root / "docs" / "readme.md"
            doc_path.parent.mkdir(parents=True)
            content = b"# Readme\n\nRun `src/app.py` directly. Do not use `scripts/generate-agent-digest.py`.\n"

            linter = MarkdownLinter()
            issues = linter.lint_content(doc_path, content)
            md019 = [i for i in issues if i.rule_id == "MD019"]
            self.assertEqual(len(md019), 1)
            self.assertIn("Repository file reference 'src/app.py'", md019[0].message)


class TestMarkdownLinterFix(unittest.TestCase):
    def setUp(self) -> None:
        self.linter = MarkdownLinter()

    def test_fix_content_cleans_formatting(self) -> None:
        raw = b"# Title\r\n\n* Bullet 1   \r\n+ Bullet 2\t\n\tTab indent\n"
        fixed = self.linter.fix_content(Path("test.md"), raw)
        expected = b"# Title\n\n- Bullet 1  \n- Bullet 2\n    Tab indent\n"
        self.assertEqual(fixed, expected)

    def test_fix_content_removes_blank_line_after_subheading(self) -> None:
        raw = b"# Title\n\n## Section\n\nContent follows.\n"
        fixed = self.linter.fix_content(Path("test.md"), raw)
        expected = b"# Title\n\n## Section\nContent follows.\n"
        self.assertEqual(fixed, expected)

    def test_fix_content_removes_blank_line_before_list(self) -> None:
        raw = b"# Title\n\nIntroduces list:\n\n- Item 1\n- Item 2\n"
        fixed = self.linter.fix_content(Path("test.md"), raw)
        expected = b"# Title\n\nIntroduces list:\n- Item 1\n- Item 2\n"
        self.assertEqual(fixed, expected)

    def test_fix_content_preserves_blank_lines_between_empty_headings(self) -> None:
        raw = b"# Title\n\n## Section 1\n\n## Section 2\nContent\n"
        fixed = self.linter.fix_content(Path("test.md"), raw)
        expected = b"# Title\n\n## Section 1\n\n## Section 2\nContent\n"
        self.assertEqual(fixed, expected)

    def test_fix_content_aligns_tables(self) -> None:
        raw = b"# Title\n\n> | Symbol | Status |\n> |:---:|---|\n> | `[ ]` | ready |\n"
        fixed = self.linter.fix_content(Path("test.md"), raw)
        expected = b"# Title\n\n> | Symbol | Status |\n> | :----: | :----- |\n> | `[ ]`  | ready  |\n"
        self.assertEqual(fixed, expected)

    def test_fix_content_table_alignment_idempotence_three_passes(self) -> None:
        raw = (
            b"# Title\n\n"
            b"| ID | Task Description | Status | Align Left | Right Align |\n"
            b"|:---:|:---|:-:|---|--:|\n"
            b"| 1 | Short | `ready` | a | 100 |\n"
            b"| 222 | Very long task description to stretch column width | `in_progress` | foo bar | 999999 |\n"
            b"| 3 | Another item | `completed` | test | 0 |\n"
        )
        # Pass 1
        pass1 = self.linter.fix_content(Path("test.md"), raw)
        self.assertNotEqual(pass1, raw)
        issues1 = self.linter.lint_content(Path("test.md"), pass1)
        self.assertEqual([i for i in issues1 if i.rule_id == "MD017"], [])

        # Pass 2: zero changes
        pass2 = self.linter.fix_content(Path("test.md"), pass1)
        self.assertEqual(pass2, pass1)

        # Pass 3: zero changes
        pass3 = self.linter.fix_content(Path("test.md"), pass2)
        self.assertEqual(pass3, pass1)


class TestEngineModuleIsolation(unittest.TestCase):
    def test_engine_module_does_not_load_argparse_or_cli(self) -> None:
        src_dir = Path(__file__).resolve().parent.parent / "src" / "support_python"
        script = (
            "import sys, types\n"
            f"pkg = types.ModuleType('support_python')\n"
            f"pkg.__path__ = [{str(src_dir)!r}]\n"
            "sys.modules['support_python'] = pkg\n"
            "sys.modules.pop('argparse', None)\n"
            "import support_python.markdown.lint as lint\n"
            "assert 'argparse' not in sys.modules, 'argparse was loaded'\n"
            "assert 'support_python.cli' not in sys.modules, 'support_python.cli was loaded'\n"
            "assert 'support_python.tools.lint_markdown' not in sys.modules\n"
            "assert not hasattr(lint, 'build_harness')\n"
            "assert not hasattr(lint, 'main')\n"
            "assert not hasattr(lint, 'TOOL_NAME')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_markdown_lint_module_removed(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("support_python.markdown_lint")


@unittest.skipUnless(shutil.which("git"), "git executable not available")
class TestDiscoverMarkdownFilesGitIgnore(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "logs" / "sub").mkdir(parents=True)
        (self.root / ".gitignore").write_text("ignored.md\nlogs/\n", encoding="utf-8")
        for name in ("kept.md", "ignored.md", "logs/sub/session.md"):
            (self.root / name).write_text("# Title\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git_init(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def test_directory_walk_skips_git_ignored_files(self) -> None:
        self._git_init()
        files = lint_markdown.discover_markdown_files([self.root], self.root, [])
        self.assertEqual(files, [self.root / "kept.md"])

    def test_explicitly_named_ignored_file_is_linted(self) -> None:
        self._git_init()
        target = self.root / "ignored.md"
        files = lint_markdown.discover_markdown_files([target], self.root, [])
        self.assertEqual(files, [target])

    def test_outside_git_repo_lints_every_file(self) -> None:
        with patch.dict("os.environ", {"GIT_CEILING_DIRECTORIES": str(self.root.parent)}):
            files = lint_markdown.discover_markdown_files([self.root], self.root, [])
        expected = sorted([self.root / "kept.md", self.root / "ignored.md", self.root / "logs" / "sub" / "session.md"])
        self.assertEqual(files, expected)

    def test_missing_git_executable_lints_every_file(self) -> None:
        self._git_init()
        with patch.object(lint_markdown.subprocess, "run", side_effect=FileNotFoundError("git")):
            files = lint_markdown.discover_markdown_files([self.root], self.root, [])
        expected = sorted([self.root / "kept.md", self.root / "ignored.md", self.root / "logs" / "sub" / "session.md"])
        self.assertEqual(files, expected)

    def test_exclude_still_applies_alongside_git_ignore(self) -> None:
        self._git_init()
        (self.root / "draft.md").write_text("# Draft\n", encoding="utf-8")
        files = lint_markdown.discover_markdown_files([self.root], self.root, ["draft.md"])
        self.assertEqual(files, [self.root / "kept.md"])

    def test_symlink_resolving_outside_walked_directory_is_linted(self) -> None:
        self._git_init()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "shared.md").write_text("# Shared\n", encoding="utf-8")
        walked = self.root / "walked"
        walked.mkdir()
        (walked / "kept.md").write_text("# Kept\n", encoding="utf-8")
        try:
            (walked / "link.md").symlink_to(Path("..") / "outside" / "shared.md")
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create symlinks on this platform: {exc}")
        files = lint_markdown.discover_markdown_files([walked], self.root, [])
        self.assertEqual(files, sorted([walked / "kept.md", outside / "shared.md"]))

    def test_root_relative_link_resolves_against_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "docs").mkdir()
            (proj_root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc_file = proj_root / "sub" / "doc.md"
            doc_file.parent.mkdir()
            content = b"# Document\n\nSee [Guide](/docs/guide.md) and [Missing](/docs/missing.md).\n"
            issues = MarkdownLinter().lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual(len(md014), 1)
            self.assertIn("/docs/missing.md", md014[0].message)

    def test_root_relative_link_resolves_where_a_leading_slash_is_absolute(self) -> None:
        # POSIX treats "/docs/missing.md" as absolute; simulate that on every platform.
        original = Path.is_absolute

        def posix_is_absolute(path: Path) -> bool:
            return str(path).startswith(("/", "\\")) or original(path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "docs").mkdir()
            (proj_root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            doc_file = proj_root / "doc.md"
            content = b"# Document\n\nSee [Guide](/docs/guide.md) and [Missing](/docs/missing.md).\n"
            with patch.object(Path, "is_absolute", posix_is_absolute):
                issues = MarkdownLinter().lint_content(doc_file, content)
            md014 = [i for i in issues if i.rule_id == "MD014"]
            self.assertEqual([("/docs/missing.md" in i.message) for i in md014], [True])


class TestChangelogReleasedHeadings(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.proj_root = Path(self._tmp.name).resolve()
        (self.proj_root / ".git").mkdir()
        (self.proj_root / "scripts").mkdir()
        (self.proj_root / "scripts" / "lint-markdown.py").write_text("# script\n", encoding="utf-8")
        self.linter = MarkdownLinter(project_root=self.proj_root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_released_date_tag_before_cutoff_exempts_md014_and_md019(self) -> None:
        content = (
            b"# Versioned Changes\n\n"
            b"## v1.0.0 [released: 2026-09-18]\n"
            b"- Docs: See [Old Link](nonexistent-file.md) in `scripts/lint-markdown.py`.\n"
        )
        issues = self.linter.lint_content(self.proj_root / "CHANGELOG.md", content)
        md014 = [i for i in issues if i.rule_id == "MD014"]
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md014, [])
        self.assertEqual(md019, [])

    def test_released_date_tag_case_insensitive(self) -> None:
        content = (
            b"# Versioned Changes\n\n"
            b"## v1.0.0 [Released: 2026-09-18]\n"
            b"- Docs: See [Old Link](nonexistent-file.md) in `scripts/lint-markdown.py`.\n"
        )
        issues = self.linter.lint_content(self.proj_root / "CHANGELOG.md", content)
        md014 = [i for i in issues if i.rule_id == "MD014"]
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(md014, [])
        self.assertEqual(md019, [])

    def test_released_date_tag_after_cutoff_flags_md014_and_md019(self) -> None:
        content = (
            b"# Versioned Changes\n\n"
            b"## v1.2.0 [released: 2026-10-15]\n"
            b"- Docs: See [Broken Link](nonexistent-file.md) in `scripts/lint-markdown.py`.\n"
        )
        issues = self.linter.lint_content(self.proj_root / "CHANGELOG.md", content)
        md014 = [i for i in issues if i.rule_id == "MD014"]
        md019 = [i for i in issues if i.rule_id == "MD019"]
        self.assertEqual(len(md014), 1)
        self.assertEqual(len(md019), 1)


if __name__ == "__main__":
    unittest.main()
