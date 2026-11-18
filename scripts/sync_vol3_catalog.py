"""Snapshot loadable Windows plugins and CLI requirements from local Vol3."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.gui-deps'))
from volatility3 import framework
from volatility3.framework.configuration import requirements
import volatility3.plugins

framework.import_files(volatility3.plugins, True)
entries = []
for name, plugin in sorted(framework.list_plugins().items()):
    if not name.startswith('windows.'):
        continue
    options = []
    for requirement in plugin.get_requirements():
        kind = type(requirement).__name__
        if kind not in {'BooleanRequirement', 'IntRequirement', 'StringRequirement', 'URIRequirement', 'ListRequirement', 'ChoiceRequirement'}:
            continue
        option = dict(name='--' + requirement.name.replace('_', '-'),
                      label=requirement.name.replace('_', ' ').replace('-', ' ').title(),
                      type='boolean' if kind == 'BooleanRequirement' else 'choice' if kind == 'ChoiceRequirement' else 'text',
                      required=not requirement.optional, help=requirement.description,
                      is_list=kind == 'ListRequirement')
        if kind == 'BooleanRequirement':
            option['default'] = bool(requirement.default)
        if kind == 'ChoiceRequirement':
            option['choices'] = list(requirement.choices)
        if kind == 'ListRequirement':
            option['element_type'] = getattr(requirement.element_type, '__name__', 'str')
        default = requirement.default
        if default is not None and default is not False:
            option['placeholder'] = ' '.join(map(str, default)) if isinstance(default, list) else str(default)
        options.append(option)
    entries.append(dict(name=name, class_name=plugin.__name__, desc=' '.join((plugin.__doc__ or name).split()),
                        deprecated='(deprecated)' in (plugin.__doc__ or '').lower(), options=options))
if len(entries) < 30:
    raise RuntimeError('Insufficient plugin metadata; existing catalog left untouched.')
(root / 'app' / 'vol3_catalog.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Synced {len(entries)} loadable Windows plugins.')
