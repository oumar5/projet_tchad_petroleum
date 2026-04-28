import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/blocks_providers.dart';

/// Reusable block dropdown that reads the cached list from [blocksProvider]
/// and writes the selection to [selectedBlockProvider].
class BlockPicker extends ConsumerWidget {
  const BlockPicker({super.key, this.label = 'Bloc'});
  final String label;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final blocks = ref.watch(blocksProvider(null));
    final selected = ref.watch(selectedBlockProvider);

    return blocks.when(
      loading: () => InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: const Icon(Icons.layers_rounded),
        ),
        child: const SizedBox(
          height: 18,
          width: 18,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
      error: (_, _) => DropdownButtonFormField<String>(
        initialValue: selected,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: const Icon(Icons.layers_rounded),
        ),
        items: const [DropdownMenuItem(value: 'X', child: Text('X (par défaut)'))],
        onChanged: (v) =>
            ref.read(selectedBlockProvider.notifier).state = v ?? 'X',
      ),
      data: (rows) {
        final values = rows.map((r) => r['code']?.toString() ?? '').toList();
        final value = values.contains(selected)
            ? selected
            : (values.isNotEmpty ? values.first : 'X');
        return DropdownButtonFormField<String>(
          initialValue: value,
          decoration: InputDecoration(
            labelText: label,
            prefixIcon: const Icon(Icons.layers_rounded),
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
