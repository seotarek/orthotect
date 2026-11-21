"""
Rule data and the violation record.

Everything here is a pure declaration: the banned-property tables and the tuple
subclass the scanners return. Keeping it free of imports means any module can
depend on it without a cycle, and the tables can be read (or generated) without
pulling in a CSS parser.
"""

class BidiViolation(tuple):
    """
    Backwards-compatible 3-tuple (line, content, suggestion) with extended metadata.

    `rule` is the registry id of the rule that fired. It is set at the detection
    site — the only place that knows which branch actually matched — rather than
    re-derived downstream from the label. Inferring it from text would mean a
    second copy of the detection logic living in the SARIF layer, and the two
    would drift the first time a rule is split or renamed.
    """
    def __new__(cls, line, col, name, val, suggestion, rule=None):
        content = f"{name}: {val}" if val else name
        instance = super().__new__(cls, (line, content, suggestion))
        instance.line = line
        instance.col = col
        instance.name = name
        instance.val = val
        instance.suggestion = suggestion
        instance.rule = rule
        return instance


BANNED_PROPERTIES = {
    'margin-left': 'margin-inline-start',
    'margin-right': 'margin-inline-end',
    'padding-left': 'padding-inline-start',
    'padding-right': 'padding-inline-end',
    'border-left': 'border-inline-start',
    'border-right': 'border-inline-end',
    'border-left-width': 'border-inline-start-width',
    'border-right-width': 'border-inline-end-width',
    'border-left-style': 'border-inline-start-style',
    'border-right-style': 'border-inline-end-style',
    'border-left-color': 'border-inline-start-color',
    'border-right-color': 'border-inline-end-color',
    'border-top-left-radius': 'border-start-start-radius',
    'border-top-right-radius': 'border-start-end-radius',
    'border-bottom-left-radius': 'border-end-start-radius',
    'border-bottom-right-radius': 'border-end-end-radius',
}


BANNED_CAMELCASE_PROPERTIES = {
    'marginLeft': 'marginInlineStart',
    'marginRight': 'marginInlineEnd',
    'paddingLeft': 'paddingInlineStart',
    'paddingRight': 'paddingInlineEnd',
    'borderLeft': 'borderInlineStart',
    'borderRight': 'borderInlineEnd',
    'borderLeftWidth': 'borderInlineStartWidth',
    'borderRightWidth': 'borderInlineEndWidth',
    'borderLeftStyle': 'borderInlineStartStyle',
    'borderRightStyle': 'borderInlineEndStyle',
    'borderLeftColor': 'borderInlineStartColor',
    'borderRightColor': 'borderInlineEndColor',
    'borderTopLeftRadius': 'borderStartStartRadius',
    'borderTopRightRadius': 'borderStartEndRadius',
    'borderBottomLeftRadius': 'borderEndStartRadius',
    'borderBottomRightRadius': 'borderEndEndRadius',
}


ALLOWED_OFFSETS = {'auto', 'inherit', 'initial', 'unset', 'revert'}


SHORTHAND_PROPERTIES = ('margin', 'padding', 'border-width', 'border-style', 'border-color', 'inset', 'scroll-margin', 'scroll-padding')
