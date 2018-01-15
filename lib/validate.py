import argparse
from sfzparser import SFZFile


def errors_for_region(region):
    attrs = region.attributes
    if 'lovel' in attrs and 'hivel' in attrs:
        if int(attrs['lovel']) > int(attrs['hivel']):
            yield "lovel (%s) of note %s is higher than hivel (%s)" % (
                attrs['lovel'], attrs['key'], attrs['hivel']
            )


def errors_for_groups(*groups):
    regions = sum([group.flattened_regions() for group in groups], [])
    return sum([list(errors_for_region(region)) for region in regions], [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='validate (partial) correctness of sfz files'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        sfz = SFZFile(open(filename).read())
        errors = errors_for_groups(*sfz.groups)

        if errors:
            print "Found", len(errors), "errors in", filename
        for error in errors:
            print "\t", error
