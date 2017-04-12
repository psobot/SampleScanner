def map_xfvel(regions):
    for region in regions:
        region.attributes.update({
            'hivel': region.attributes['xfin_hivel'],
            'lovel': region.attributes['xfin_lovel'],
        })
        del region.attributes['xfin_hivel']
        del region.attributes['xfin_lovel']
        del region.attributes['xfout_hivel']
        del region.attributes['xfout_lovel']
        yield region
