# gemato: Profile behavior tests
# vim:fileencoding=utf-8
# (c) 2017 Michał Górny
# Licensed under the terms of 2-clause BSD license

import os.path

import gemato.profile

from tests.testutil import TempDirTestCase


class EbuildRepositoryTests(TempDirTestCase):
    """
    Tests for ebuild repository profiles.
    """

    PROFILE = gemato.profile.EbuildRepositoryProfile
    DIRS = [
        'dev-foo',
        'dev-foo/bar',
        'dev-foo/bar/files',
        'eclass',
        'eclass/tests',
        'licenses',
        'metadata',
        'metadata/dtd',
        'metadata/glsa',
        'metadata/install-qa-check.d',
        'metadata/md5-cache',
        'metadata/md5-cache/dev-foo',
        'metadata/news',
        'metadata/news/2020-01-01-foo',
        'metadata/xml-schema',
        'profiles',
        'profiles/arch',
        'profiles/arch/foo',
        'profiles/desc',
        'profiles/updates',
    ]
    EXPECTED_TYPES = {
        'header.txt': 'DATA',
        'skel.ebuild': 'DATA',
        'skel.metadata.xml': 'DATA',
        'dev-foo/metadata.xml': 'DATA',
        'dev-foo/bar/bar-1.ebuild': 'DATA',
        'dev-foo/bar/metadata.xml': 'DATA',
        'dev-foo/bar/files/test.patch': 'DATA',
        'eclass/foo.eclass': 'DATA',
        'eclass/tests/foo.sh': 'DATA',
        'licenses/foo': 'DATA',
        'metadata/layout.conf': 'DATA',
        'metadata/projects.xml': 'DATA',
        'metadata/pkg_desc_index': 'DATA',
        'metadata/timestamp': 'DATA',
        'metadata/timestamp.chk': 'DATA',
        'metadata/timestamp.commit': 'DATA',
        'metadata/timestamp.x': 'DATA',
        'metadata/dtd/foo.dtd': 'DATA',
        'metadata/glsa/glsa-202001-01.xml': 'DATA',
        'metadata/install-qa-check.d/50foo': 'DATA',
        'metadata/md5-cache/dev-foo/bar-1': 'DATA',
        'metadata/news/2020-01-01-foo/2020-01-01-foo.en.txt': 'DATA',
        'metadata/news/2020-01-01-foo/2020-01-01-foo.en.txt.asc': 'DATA',
        'metadata/xml-schema/foo.xsd': 'DATA',
        'profiles/arch.desc': 'DATA',
        'profiles/categories': 'DATA',
        'profiles/eapi': 'DATA',
        'profiles/info_pkgs': 'DATA',
        'profiles/info_vars': 'DATA',
        'profiles/license_groups': 'DATA',
        'profiles/package.mask': 'DATA',
        'profiles/profiles.desc': 'DATA',
        'profiles/repo_name': 'DATA',
        'profiles/thirdpartymirrors': 'DATA',
        'profiles/use.desc': 'DATA',
        'profiles/use.local.desc': 'DATA',
        'profiles/arch/foo/eapi': 'DATA',
        'profiles/arch/foo/parent': 'DATA',
        'profiles/desc/foo.desc': 'DATA',
        'profiles/updates/1Q-2020': 'DATA',
    }
    FILES = dict.fromkeys(EXPECTED_TYPES, u'')

    def test_get_entry_type_for_path(self):
        p = self.PROFILE()
        for f, expt in self.EXPECTED_TYPES.items():
            self.assertEqual(
                    p.get_entry_type_for_path(f),
                    expt,
                    "type mismatch for {}".format(f))

    def test_update_entries_for_directory(self):
        m = gemato.recursiveloader.ManifestRecursiveLoader(
                os.path.join(self.dir, 'Manifest'),
                hashes=['SHA256', 'SHA512'],
                allow_create=True,
                profile=self.PROFILE())
        m.update_entries_for_directory('')
        for f, expt in self.EXPECTED_TYPES.items():
            self.assertEqual(
                    m.find_path_entry(f).tag,
                    expt,
                    "type mismatch for {}".format(f))
        return m

class BackwardsCompatEbuildRepositoryTests(EbuildRepositoryTests):
    PROFILE = gemato.profile.BackwardsCompatEbuildRepositoryProfile

    def __init__(self, *args, **kwargs):
        self.EXPECTED_TYPES = self.EXPECTED_TYPES.copy()
        self.EXPECTED_TYPES.update({
            'dev-foo/bar/bar-1.ebuild': 'EBUILD',
            'dev-foo/bar/metadata.xml': 'MISC',
            'dev-foo/bar/files/test.patch': 'AUX',
        })
        # TODO: this is only temporary until we have API to create
        # the Manifest at this level automatically
        self.FILES['dev-foo/bar/Manifest'] = u''
        super(BackwardsCompatEbuildRepositoryTests, self).__init__(
                *args, **kwargs)

    def test_update_entries_for_directory(self):
        m = (super(BackwardsCompatEbuildRepositoryTests, self)
                .test_update_entries_for_directory())
        self.assertEqual(
                m.find_path_entry('dev-foo/bar/files/test.patch').path,
                'files/test.patch')
        self.assertEqual(
                m.find_path_entry('dev-foo/bar/files/test.patch').aux_path,
                'test.patch')