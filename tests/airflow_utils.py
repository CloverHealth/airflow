"""Tests for the airflow.utils module."""

import unittest

from airflow import utils


class TestETLLoggingFormatting(unittest.TestCase):
    """Test error string formatting.

    This is copied from the clover repo minus the part that tests SQLAlchemy to
    psycopg2 exception translation because it'd be a pain to port that stuff
    over here just to test what we know works.
    """
    def setUp(self):
        super().setUp()
        logging.basicConfig(level=logging.INFO)

    def test_falsy(self):
        """Make sure that anything falsy passed in results in None."""
        self.assertIsNone(utils.format_error(None))
        self.assertIsNone(utils.format_error(0))

    def test_nonexception(self):
        """Anything not an Exception should be returned as the str of itself."""
        test_objects = (
            1,
            3.14,
            'foo',
            {'bar', 'baz'},
            {'key': 'value'},
            self.setUp,
            self,
            datetime
        )

        for obj in test_objects:
            self.assertEqual(utils.format_error(obj), str(obj))

    def test_keyboardinterrupt(self):
        """Fixed result for KeyboardInterrupt."""
        exc = KeyboardInterrupt()
        self.assertEqual(utils.format_error(exc),
                         '(KeyboardInterrupt) Manually killed by user.')

        exc = KeyboardInterrupt("Python doesn't use exception messages for this.")
        self.assertEqual(utils.format_error(exc),
                         '(KeyboardInterrupt) Manually killed by user.')

    def test_without_cause(self):
        """No cause --> shouldn't have extra information."""
        exc = ValueError('Something is broken.')
        self.assertEqual(utils.format_error(exc),
                         '(ValueError) Something is broken.')
        self.assertEqual(utils.format_error(exc, verbose=False),
                         'Something is broken.')

    def test_with_cause(self):
        """Cause found --> additional information."""
        exc = RuntimeError('Something exploded.')
        exc.__cause__ = OSError('File not found.')

        self.assertEqual(utils.format_error(exc),
                         '(RuntimeError from OSError) Something exploded.')
        self.assertEqual(utils.format_error(exc, verbose=False),
                         'Something exploded.')

    def test_with_self_cause(self):
        """Happens when an exception is improperly re-raised."""
        exc = RuntimeError('BOOM')
        exc.__cause__ = exc

        self.assertEqual(utils.format_error(exc), '(RuntimeError) BOOM')

    def test_with_traceback(self):
        """Test that there's *something* after the error message when we ask for a traceback."""
        try:
            raise RuntimeError('BOOM')
        except RuntimeError as exc:
            message = utils.format_error(exc, include_trace=True)
            self.assertRegex(message, r'(?m)^\(RuntimeError\) BOOM\n.+$')

    def test_with_traceback_unverbose(self):
        """We should still get a traceback even if verbose is False."""
        try:
            raise RuntimeError('BOOM')
        except RuntimeError as exc:
            message = utils.format_error(exc, verbose=False, include_trace=True)
            self.assertRegex(message, r'(?m)^BOOM\n.+$')


class TestPHIStripping(unittest.TestCase):
    """Test how we strip PHI out of strings."""
    def test_hicn(self):
        # No dashes
        self.assertEqual(utils.remove_sensitive_data('123456789AbC'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123456789a'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123456789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('A123456789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('.A123456789a.'), '.[REDACTED].')

        # Add dashes
        self.assertEqual(utils.remove_sensitive_data('123-45-6789AbC'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123-45-6789a'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123-45-6789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('A123-45-6789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('.A123-45-6789a.'), '.[REDACTED].')

        # Multiple ones in one string
        self.assertEqual(utils.remove_sensitive_data('123-45-6789AbC ! 098-76-5432'),
                                                     '[REDACTED] ! [REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123-45-6789-098765432 '),
                                                     '[REDACTED]-[REDACTED] ')

    def test_rrb(self):
        # Some RRBs look like HICNs so we don't need to test the 9-digit ones.
        self.assertEqual(utils.remove_sensitive_data('123456ABC'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123456A'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123456'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('A123456'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('.A123456A.'), '.[REDACTED].')

        # Multiple ones in one string
        self.assertEqual(utils.remove_sensitive_data('123-45-6789AbC ! 098765QR'),
                                                     '[REDACTED] ! [REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('A123456-098765z '),
                                                     '[REDACTED]-[REDACTED] ')

    def test_ssn(self):
        self.assertEqual(utils.remove_sensitive_data('123-45-6789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123456789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('.123-45-6789.'), '.[REDACTED].')

        self.assertEqual(utils.remove_sensitive_data('098-76-5432 a!bc 123456789'),
                                                     '[REDACTED] a!bc [REDACTED]')

    def test_phone(self):
        self.assertEqual(utils.remove_sensitive_data('123-456-6789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('1234567890'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('(123) 456-7890'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123/456-7890'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123-456-7890'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('123  456 7890'), '[REDACTED]')

        self.assertEqual(utils.remove_sensitive_data('123-456-6789x5896'), '[REDACTED]x5896')
        self.assertEqual(utils.remove_sensitive_data('1234567890 ? !@# 12 q10987654321'),
                                                     '[REDACTED] ? !@# 12 q[REDACTED]1')

    def test_cpid(self):
        self.assertEqual(utils.remove_sensitive_data('CP1'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('CP123456789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('cP123456789'), '[REDACTED]')
        self.assertEqual(utils.remove_sensitive_data('  cP1234567 89'), '  [REDACTED] 89')
        self.assertEqual(utils.remove_sensitive_data('cP123456789CP098765432'),
                                                     '[REDACTED][REDACTED]')

    def test_combos(self):
        """Test all the things!"""
        self.assertEqual(utils.remove_sensitive_data('CP123456789 = 123-45-6789'),
                                                     '[REDACTED] = [REDACTED]')
        self.assertEqual(utils.remove_sensitive_data(
            'HICN 098765ABC has phone 880/555-1845 and SSN 999-99-9999!'),
            'HICN [REDACTED] has phone [REDACTED] and SSN [REDACTED]!')
