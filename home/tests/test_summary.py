from django.test import TransactionTestCase
from home.zulip_helpers import create_summary


class ZulipSummaryTestCase(TransactionTestCase):
    def test_nested_tags(self):
        input = '<p>In this post, I want to kind of bring together the theme of curvature and the theme of affine or projective geometry. My goal is to introduce the <em>spaces of constant curvature</em> in a unified way as subspaces of Euclidean space and explore their symmetries as groups of matrices.</p>'
        expected = '\n```quote\nIn this post, I want to kind of bring together the theme of curvature and the theme of affine or projective geometry. My goal is to introduce the *spaces of constant curva...*\n```'
        # formatting of nested tags is preserved
        actual = create_summary(input, 150)
        self.assertEqual(expected, actual)
