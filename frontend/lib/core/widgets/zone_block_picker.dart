import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/blocks_providers.dart';

/// Cascading Zone → Block picker. The selected zone code is held in
/// [selectedZoneProvider] and the selected block code in [selectedBlockProvider].
class ZoneBlockPicker extends ConsumerWidget {
  const ZoneBlockPicker({super.key, this.stackBelow = 480});

  /// Stack the two dropdowns vertically when the available width is below
  /// this many pixels.
  final double stackBelow;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return LayoutBuilder(
      builder: (ctx, c) {
        final stack = c.maxWidth < stackBelow;
        final zone = _ZoneDropdown();
        final block = _BlockDropdown();
        if (stack) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [zone, const SizedBox(height: 12), block],
          );
        }
        return Row(
          children: [
            Expanded(child: zone),
            const SizedBox(width: 12),
            Expanded(child: block),
          ],
        );
      },
    );
  }
}

class _ZoneDropdown extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final zones = ref.watch(zonesProvider);
    final selected = ref.watch(selectedZoneProvider);

    return zones.when(
      loading: () => const _LoadingField(label: 'Zone'),
      error: (_, _) => DropdownButtonFormField<String?>(
        initialValue: selected,
        decoration: const InputDecoration(
          labelText: 'Zone',
          prefixIcon: Icon(Icons.public_rounded),
        ),
        items: const [DropdownMenuItem(value: null, child: Text('—'))],
        onChanged: null,
      ),
      data: (rows) {
        final values = rows.map((z) => z['code']?.toString() ?? '').toList();
        final value = values.contains(selected) ? selected : null;
        return DropdownButtonFormField<String?>(
          initialValue: value,
          decoration: const InputDecoration(
            labelText: 'Zone',
            prefixIcon: Icon(Icons.public_rounded),
          ),
          items: [
            const DropdownMenuItem(value: null, child: Text('Toutes les zones')),
            for (final z in rows)
              DropdownMenuItem(
                value: z['code']?.toString() ?? '',
                child: Text('${z['code']} — ${z['name']}'),
              ),
          ],
          onChanged: (v) {
            ref.read(selectedZoneProvider.notifier).state = v;
          },
        );
      },
    );
  }
}

class _BlockDropdown extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final zone = ref.watch(selectedZoneProvider);
    final blocks = ref.watch(blocksProvider(zone));
    final selected = ref.watch(selectedBlockProvider);

    return blocks.when(
      loading: () => const _LoadingField(label: 'Bloc'),
      error: (_, _) => const _DisabledField(
        label: 'Bloc', hint: 'Erreur de chargement',
      ),
      data: (rows) {
        if (rows.isEmpty) {
          return const _DisabledField(
            label: 'Bloc',
            hint: 'Aucun bloc dans cette zone',
          );
        }
        final values = rows.map((r) => r['code']?.toString() ?? '').toList();
        final value = values.contains(selected) ? selected : values.first;
        // If we had to fall back to the first value, sync the provider so the
        // upstream consumers see the actual selection.
        if (value != selected) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            ref.read(selectedBlockProvider.notifier).state = value;
          });
        }
        return DropdownButtonFormField<String>(
          initialValue: value,
          decoration: const InputDecoration(
            labelText: 'Bloc',
            prefixIcon: Icon(Icons.layers_rounded),
          ),
          items: [
            for (final r in rows)
              DropdownMenuItem(
                value: r['code']?.toString() ?? '',
                child: Text(
                  r['name']?.toString().isNotEmpty == true
                      ? '${r['code']} — ${r['name']}'
                      : r['code']?.toString() ?? '',
                ),
              ),
          ],
          onChanged: (v) {
            if (v != null) {
              ref.read(selectedBlockProvider.notifier).state = v;
            }
          },
        );
      },
    );
  }
}

class _LoadingField extends StatelessWidget {
  const _LoadingField({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(label == 'Zone' ? Icons.public_rounded : Icons.layers_rounded),
      ),
      child: const SizedBox(
        height: 18,
        width: 18,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
    );
  }
}

class _DisabledField extends StatelessWidget {
  const _DisabledField({required this.label, required this.hint});
  final String label;
  final String hint;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(Icons.layers_rounded),
        enabled: false,
      ),
      child: Text(
        hint,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
    );
  }
}
