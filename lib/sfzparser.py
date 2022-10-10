import os
import re

comments = re.compile(r'//.*$', re.M)
lookfor = re.compile(r'<(\w+)>|(\w+)=([^\s]+)')


class SFZFile(object):
    def __init__(self, text=None):
        if text:
            self.groups = self.parse(text)
        else:
            self.groups = []

    def parse(self, text):
        groups = []
        groupdata = {}
        current_group_regions = []
        regiondata = {}

        text = re.sub(comments, '', text)

        current = None

        for m in re.finditer(lookfor, text):
            if m.group(1) in ['group', 'region']:
                if m.group(1) == 'group':
                    if groupdata != {}:
                        if regiondata != {}:
                            region = Region(regiondata)
                            current_group_regions.append(region)
                            regiondata = {}
                        group = Group(groupdata, current_group_regions)
                        groups.append(group)
                    groupdata = {}
                    current_group_regions = []
                    current = groupdata
                elif m.group(1) == 'region':
                    if regiondata != {}:
                        region = Region(regiondata)
                        current_group_regions.append(region)
                    regiondata = {}
                    current = regiondata
            else:
                current[m.group(2)] = m.group(3)

        if len(groups) == 0:
            if regiondata != {}:
                current_group_regions.append(Region(regiondata))
            return [Group({}, current_group_regions)]
        else:
            groups[-1].regions.append(Region(regiondata))
            return groups


class Group(object):
    def __init__(self, attributes, regions):
        self.attributes = attributes
        self.regions = regions

    def flattened_regions(self):
        return [region.merge(self.attributes) for region in self.regions]

    def just_group(self):
        return "\n".join(
            ["<group>"] +
            ['%s=%s' % (k, v) for k, v in self.attributes.items()]
        )

    def __repr__(self):
        return "<Group %s with regions:\n\t%s>" % (
            repr(self.attributes),
            repr(self.regions)
        )

    def __str__(self):
        return self.just_group() + "\n" + "\n\n".join([
            str(r) for r in self.regions
        ])


class Region(object):
    def __init__(self, attributes):
        self.attributes = attributes

    def __repr__(self):
        return "<Region %s>" % (
            repr(self.attributes)
        )

    def __str__(self):
        return "\n".join(
            ["<region>"] +
            ['%s=%s' % (k, v) for k, v in self.attributes.items()]
        )

    def exists(self, root=None):
        sample_path = self.attributes['sample']
        if root:
            sample_path = os.path.join(root, sample_path)
        return os.path.isfile(sample_path)

    def without_attributes(self, discard=lambda x: False):
        return Region(dict([
            (k, v)
            for k, v in self.attributes.items()
            if not discard(k)
        ]))

    def merge(self, other_attrs):
        return Region(dict(
            (k, v)
            for d in [self.attributes, other_attrs]
            for k, v in d.items()
        ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='parse SFZ files')
    parser.add_argument('files', type=str, help='files to parse', nargs='+')
    args = parser.parse_args()

    for fn in args.files:
        file = SFZFile(open(fn).read())
        for group in file.groups:
            print(group)
