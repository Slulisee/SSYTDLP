import unittest
from themes import COLOR_KEYS, THEMES, appearance_settings, contrast, palette, valid_color


class ThemeTests(unittest.TestCase):
    def test_previous_themes_migrate_and_bad_custom_values_are_ignored(self):
        self.assertEqual(appearance_settings({'theme':'dark'})[0],'ocean')
        self.assertEqual(appearance_settings({'theme':'light'})[0],'frost')
        self.assertEqual(appearance_settings({'theme':'missing','theme_colors':[]}),('ocean',{}))
        self.assertEqual(appearance_settings({'theme':'carbon','theme_colors':{'accent':'#AABBCC','bg':'bad','other':'#111111'}}),('carbon',{'accent':'#aabbcc'}))

    def test_all_themes_have_visible_text_and_checkbox_marks(self):
        self.assertEqual(len(THEMES),16)
        for key in THEMES:
            colors=palette(key)
            with self.subTest(theme=key):
                self.assertTrue(all(valid_color(colors[name]) for name in COLOR_KEYS))
                self.assertGreaterEqual(contrast(colors['text'],colors['panel']),4.5)
                self.assertGreaterEqual(contrast(colors['muted'],colors['panel']),3)
                self.assertGreaterEqual(contrast(colors['on_accent'],colors['accent']),3)
                self.assertGreaterEqual(contrast(colors['icon'],colors['panel']),3)
                self.assertNotEqual(colors['accent'],colors['field'])

    def test_custom_tokens_recolor_derived_controls_without_mutating_the_theme(self):
        original=palette('ocean')
        custom=palette('ocean',{'accent':'#dd5500','panel':'#222222','bg':'#121212','other':'#000000'})
        self.assertEqual(custom['accent'],'#dd5500')
        self.assertNotEqual(custom['selected'],original['selected'])
        self.assertNotEqual(custom['button'],original['button'])
        self.assertEqual(palette('ocean'),original)
        self.assertTrue(all(value[1:3]==value[3:5]==value[5:7] for value in palette('carbon').values() if isinstance(value,str)))


if __name__=='__main__':unittest.main()
