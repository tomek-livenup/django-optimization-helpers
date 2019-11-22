class optimize_related(object):
    """
    from optimization_helper.decorators import optimize_related
    """

    def __init__(self, select_related=None, prefetch_related=None, annotate=None):
        super(optimize_related, self).__init__()
        self.select_related = select_related
        self.prefetch_related = prefetch_related
        self.annotate = annotate

    def __call__(self, target):
        target._optimize_related = dict(
            select_related=self.select_related or "",
            prefetch_related=self.prefetch_related or "",
            annotate=self.annotate or ""
        )
        return target
