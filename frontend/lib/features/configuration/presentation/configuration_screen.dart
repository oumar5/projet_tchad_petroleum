import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/providers/blocks_providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/section_header.dart';

class ConfigurationScreen extends ConsumerWidget {
  const ConfigurationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Configuration'),
          bottom: const TabBar(
            indicatorWeight: 3,
            labelStyle: TextStyle(fontWeight: FontWeight.w700),
            tabs: [
              Tab(icon: Icon(Icons.layers_rounded), text: 'Blocs'),
              Tab(icon: Icon(Icons.opacity_rounded), text: 'Puits'),
            ],
          ),
        ),
        body: const TabBarView(children: [_BlocksTab(), _WellsTab()]),
      ),
    );
  }
}

// ----------------------------------------------------------------------------
// Blocks
// ----------------------------------------------------------------------------

class _BlocksTab extends ConsumerWidget {
  const _BlocksTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final blocks = ref.watch(blocksProvider);
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab-block',
        onPressed: () => _showBlockDialog(context, ref),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nouveau bloc'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(blocksProvider),
        child: blocks.when(
          loading: () => ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: 4,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, _) => const Skeleton(height: 80, radius: 12),
          ),
          error: (e, _) =>
              ErrorState(error: e, onRetry: () => ref.invalidate(blocksProvider)),
          data: (rows) {
            if (rows.isEmpty) {
              return EmptyState(
                icon: Icons.layers_outlined,
                title: 'Aucun bloc défini',
                subtitle:
                    'Crée le premier bloc de production de la zone.',
                action: FilledButton.icon(
                  onPressed: () => _showBlockDialog(context, ref),
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Ajouter un bloc'),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              itemCount: rows.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _BlockCard(
                row: rows[i],
                onEdit: () => _showBlockDialog(context, ref, existing: rows[i]),
                onDelete: () => _confirmDelete(context, ref, rows[i]),
              ),
            );
          },
        ),
      ),
    );
  }

  void _showBlockDialog(
    BuildContext context,
    WidgetRef ref, {
    Map<String, dynamic>? existing,
  }) {
    showDialog(
      context: context,
      builder: (_) => _BlockFormDialog(existing: existing),
    );
  }

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    Map<String, dynamic> block,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Supprimer ce bloc ?'),
        content: Text(
          'Le bloc ${block['code']} sera retiré. '
          'Si des données ou des puits y sont rattachés, la suppression sera refusée.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.dangerRed,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref
          .read(blocksRepositoryProvider)
          .deleteBlock(block['id'].toString());
      ref.invalidate(blocksProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Bloc supprimé')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(prettyError(e))),
      );
    }
  }
}

class _BlockCard extends StatelessWidget {
  const _BlockCard({
    required this.row,
    required this.onEdit,
    required this.onDelete,
  });
  final Map<String, dynamic> row;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: scheme.primary.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Text(
                (row['code'] ?? '?').toString(),
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: scheme.primary,
                  fontSize: 16,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    row['name']?.toString() ?? '—',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (row['description'] != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      row['description'].toString(),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            IconButton(
              tooltip: 'Modifier',
              icon: const Icon(Icons.edit_outlined, size: 20),
              onPressed: onEdit,
            ),
            IconButton(
              tooltip: 'Supprimer',
              icon: Icon(Icons.delete_outline_rounded,
                  size: 20, color: AppColors.dangerRed),
              onPressed: onDelete,
            ),
          ],
        ),
      ),
    );
  }
}

class _BlockFormDialog extends ConsumerStatefulWidget {
  const _BlockFormDialog({this.existing});
  final Map<String, dynamic>? existing;

  @override
  ConsumerState<_BlockFormDialog> createState() => _BlockFormDialogState();
}

class _BlockFormDialogState extends ConsumerState<_BlockFormDialog> {
  late final TextEditingController _code = TextEditingController(
    text: widget.existing?['code']?.toString() ?? '',
  );
  late final TextEditingController _name = TextEditingController(
    text: widget.existing?['name']?.toString() ?? '',
  );
  late final TextEditingController _desc = TextEditingController(
    text: widget.existing?['description']?.toString() ?? '',
  );
  bool _saving = false;

  bool get _isEdit => widget.existing != null;

  @override
  void dispose() {
    _code.dispose();
    _name.dispose();
    _desc.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _saving = true);
    try {
      final repo = ref.read(blocksRepositoryProvider);
      if (_isEdit) {
        await repo.updateBlock(
          blockId: widget.existing!['id'].toString(),
          name: _name.text.trim(),
          description: _desc.text.trim().isEmpty ? null : _desc.text.trim(),
        );
      } else {
        await repo.createBlock(
          code: _code.text.trim(),
          name: _name.text.trim(),
          description: _desc.text.trim().isEmpty ? null : _desc.text.trim(),
        );
      }
      ref.invalidate(blocksProvider);
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_isEdit ? 'Bloc mis à jour' : 'Bloc créé')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(prettyError(e))),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(_isEdit ? 'Modifier le bloc' : 'Nouveau bloc'),
      content: SizedBox(
        width: 380,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _code,
              enabled: !_isEdit,
              decoration: const InputDecoration(
                labelText: 'Code (ex. X, Y, NORD-1)',
                helperText: 'Identifiant court — non modifiable',
              ),
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: 'Nom complet'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _desc,
              decoration: const InputDecoration(
                labelText: 'Description (optionnel)',
              ),
              maxLines: 2,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: _saving ? null : _submit,
          child: _saving
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(_isEdit ? 'Enregistrer' : 'Créer'),
        ),
      ],
    );
  }
}

// ----------------------------------------------------------------------------
// Wells
// ----------------------------------------------------------------------------

class _WellsTab extends ConsumerWidget {
  const _WellsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final wells = ref.watch(wellsProvider(null));
    final blocks = ref.watch(blocksProvider);
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab-well',
        onPressed: blocks.value == null || blocks.value!.isEmpty
            ? null
            : () => _showWellDialog(context, ref, blocks: blocks.value!),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nouveau puits'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(wellsProvider(null)),
        child: wells.when(
          loading: () => ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: 4,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, _) => const Skeleton(height: 76, radius: 12),
          ),
          error: (e, _) => ErrorState(
              error: e, onRetry: () => ref.invalidate(wellsProvider(null))),
          data: (rows) {
            if (rows.isEmpty) {
              return EmptyState(
                icon: Icons.opacity_outlined,
                title: 'Aucun puits déclaré',
                subtitle:
                    'Ajoute le premier puits attaché à un bloc existant.',
                action: blocks.value == null || blocks.value!.isEmpty
                    ? null
                    : FilledButton.icon(
                        onPressed: () => _showWellDialog(context, ref,
                            blocks: blocks.value!),
                        icon: const Icon(Icons.add_rounded),
                        label: const Text('Ajouter un puits'),
                      ),
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                const SectionHeader(
                  title: 'Puits enregistrés',
                  subtitle: 'Triés par code',
                ),
                for (final w in rows)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _WellCard(
                      row: w,
                      blocks: blocks.value ?? const [],
                      onEdit: () => _showWellDialog(
                        context, ref,
                        blocks: blocks.value ?? const [],
                        existing: w,
                      ),
                      onDelete: () => _confirmDeleteWell(context, ref, w),
                    ),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }

  void _showWellDialog(
    BuildContext context,
    WidgetRef ref, {
    required List<Map<String, dynamic>> blocks,
    Map<String, dynamic>? existing,
  }) {
    showDialog(
      context: context,
      builder: (_) => _WellFormDialog(blocks: blocks, existing: existing),
    );
  }

  Future<void> _confirmDeleteWell(
    BuildContext context,
    WidgetRef ref,
    Map<String, dynamic> well,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Supprimer ce puits ?'),
        content: Text(
          'Le puits ${well['code']} sera retiré. '
          'Si des données de production y sont rattachées, la suppression sera refusée.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.dangerRed,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref
          .read(blocksRepositoryProvider)
          .deleteWell(well['id'].toString());
      ref.invalidate(wellsProvider(null));
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Puits supprimé')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(prettyError(e))),
      );
    }
  }
}

class _WellCard extends StatelessWidget {
  const _WellCard({
    required this.row,
    required this.blocks,
    required this.onEdit,
    required this.onDelete,
  });
  final Map<String, dynamic> row;
  final List<Map<String, dynamic>> blocks;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  String _blockCode(String blockId) {
    for (final b in blocks) {
      if (b['id']?.toString() == blockId) {
        return b['code']?.toString() ?? '—';
      }
    }
    return '—';
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final active = row['is_active'] == true;
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Icon(
              active ? Icons.opacity_rounded : Icons.opacity_outlined,
              color: active ? AppColors.tealAccent : scheme.outline,
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        row['code']?.toString() ?? '—',
                        style: Theme.of(context).textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          'Bloc ${_blockCode(row['block_id'].toString())}',
                          style: const TextStyle(
                            fontSize: 11, fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Pompe : ${row['pump_type'] ?? '—'} · '
                    '${active ? "actif" : "inactif"}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              tooltip: 'Modifier',
              icon: const Icon(Icons.edit_outlined, size: 20),
              onPressed: onEdit,
            ),
            IconButton(
              tooltip: 'Supprimer',
              icon: Icon(Icons.delete_outline_rounded,
                  size: 20, color: AppColors.dangerRed),
              onPressed: onDelete,
            ),
          ],
        ),
      ),
    );
  }
}

class _WellFormDialog extends ConsumerStatefulWidget {
  const _WellFormDialog({required this.blocks, this.existing});
  final List<Map<String, dynamic>> blocks;
  final Map<String, dynamic>? existing;

  @override
  ConsumerState<_WellFormDialog> createState() => _WellFormDialogState();
}

class _WellFormDialogState extends ConsumerState<_WellFormDialog> {
  late final TextEditingController _code = TextEditingController(
    text: widget.existing?['code']?.toString() ?? '',
  );
  late final TextEditingController _pumpType = TextEditingController(
    text: widget.existing?['pump_type']?.toString() ?? '',
  );
  late String _blockId = widget.existing?['block_id']?.toString() ??
      (widget.blocks.isNotEmpty ? widget.blocks.first['id'].toString() : '');
  late bool _active = widget.existing?['is_active'] != false;
  bool _saving = false;

  bool get _isEdit => widget.existing != null;

  @override
  void dispose() {
    _code.dispose();
    _pumpType.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _saving = true);
    try {
      final repo = ref.read(blocksRepositoryProvider);
      if (_isEdit) {
        await repo.updateWell(
          wellId: widget.existing!['id'].toString(),
          blockId: _blockId,
          pumpType: _pumpType.text.trim().isEmpty ? null : _pumpType.text.trim(),
          isActive: _active,
        );
      } else {
        await repo.createWell(
          code: _code.text.trim(),
          blockId: _blockId,
          pumpType: _pumpType.text.trim().isEmpty ? null : _pumpType.text.trim(),
          isActive: _active,
        );
      }
      ref.invalidate(wellsProvider(null));
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_isEdit ? 'Puits mis à jour' : 'Puits créé')),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(prettyError(e))),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(_isEdit ? 'Modifier le puits' : 'Nouveau puits'),
      content: SizedBox(
        width: 380,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _code,
              enabled: !_isEdit,
              decoration: const InputDecoration(
                labelText: 'Code (ex. X-01, Y-12)',
                helperText: 'Identifiant unique — non modifiable',
              ),
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _blockId,
              decoration: const InputDecoration(
                labelText: 'Bloc parent',
                prefixIcon: Icon(Icons.layers_rounded),
              ),
              items: [
                for (final b in widget.blocks)
                  DropdownMenuItem(
                    value: b['id'].toString(),
                    child: Text('${b['code']} — ${b['name']}'),
                  ),
              ],
              onChanged: (v) => setState(() => _blockId = v ?? _blockId),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _pumpType,
              decoration: const InputDecoration(
                labelText: 'Type de pompe (optionnel)',
                helperText: 'ESP, Beam, Rod, etc.',
              ),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Puits actif'),
              subtitle: const Text(
                'Décoche pour désactiver sans supprimer.',
              ),
              value: _active,
              onChanged: (v) => setState(() => _active = v),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: _saving ? null : _submit,
          child: _saving
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(_isEdit ? 'Enregistrer' : 'Créer'),
        ),
      ],
    );
  }
}
