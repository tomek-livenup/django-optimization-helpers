class optimize_related(object):
    """
    from optimization_helper.decorators import optimize_related
    """

    def __init__(self, select_related=None, prefetch_related=None):
        super(optimize_related, self).__init__()
        self.select_related = select_related
        self.prefetch_related = prefetch_related

    def __call__(self, target):
        target._optimize_related = dict(
            select_related=self.select_related,
            prefetch_related=self.prefetch_related
        )
        return target
