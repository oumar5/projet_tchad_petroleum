import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../data/production_repository.dart';

final _repoProvider = Provider<ProductionRepository>(
  (ref) => ProductionRepository(ref.watch(apiClientProvider)),
);

final _dailyProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).daily(),
);

class ProductionScreen extends ConsumerWidget {
  const ProductionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final daily = ref.watch(_dailyProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Production'),
        actions: [
          IconButton(
            tooltip: 'Actualiser',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => ref.invalidate(_dailyProvider),
          ),
          const SizedBox(width: 4),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(context, ref),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nouvelle saisie'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(_dailyProvider),
        child: daily.when(
          loading: () => const _ProductionLoading(),
          error: (e, _) => ErrorState(
            error: e,
            onRetry: () => ref.invalidate(_dailyProvider),
          ),
          data: (items) {
            if (items.isEmpty) {
              return EmptyState(
                icon: Icons.inbox_outlined,
                title: 'Aucune donnée',
                subtitle:
                    'Importe le fichier Excel ou ajoute une saisie manuelle.',
                action: FilledButton.icon(
                  onPressed: () => _showCreateDialog(context, ref),
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Ajouter'),
                ),
              );
            }
            return _ProductionList(items: items);
          },
        ),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final dateCtrl = TextEditingController(
        text: DateTime.now().toIso8601String().substring(0, 10));
    final blockCtrl = TextEditingController(text: 'X');
    final oilCtrl = TextEditingController();
    final waterCtrl = TextEditingController();
    final wcCtrl = TextEditingController();
    final wtCtrl = TextEditingController(text: '20');
    final waCtrl = TextEditingController(text: '18');

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Nouvelle saisie quotidienne'),
        content: SizedBox(
          width: 380,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _Field(controller: dateCtrl, label: 'Date (YYYY-MM-DD)'),
                _Field(controller: blockCtrl, label: 'Bloc'),
                _Field(controller: wtCtrl, label: 'Puits totaux', number: true),
                _Field(controller: waCtrl, label: 'Puits actifs', number: true),
                _Field(controller: oilCtrl, label: 'Huile (bbl)', number: true),
                _Field(controller: waterCtrl, label: 'Eau (bbl)', number: true),
                _Field(controller: wcCtrl, label: 'Watercut (%)', number: true),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () async {
              try {
                await ref.read(_repoProvider).create(
                      date: dateCtrl.text,
                      blockCode: blockCtrl.text,
                      wellsTotal: int.parse(wtCtrl.text),
                      wellsActive: int.parse(waCtrl.text),
                      oilBbl: double.parse(oilCtrl.text),
                      waterBbl: double.parse(waterCtrl.text),
                      watercutPct: double.parse(wcCtrl.text),
                    );
                if (context.mounted) Navigator.pop(context);
                ref.invalidate(_dailyProvider);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(prettyError(e))),
                  );
                }
              }
            },
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    this.number = false,
  });
  final TextEditingController controller;
  final String label;
  final bool number;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(labelText: label),
        keyboardType: number ? TextInputType.number : TextInputType.text,
      ),
    );
  }
}

class _ProductionLoading extends StatelessWidget {
  const _ProductionLoading();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 8,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (_, _) => const Skeleton(height: 76, radius: 12),
    );
  }
}

class _ProductionList extends StatelessWidget {
  const _ProductionList({required this.items});
  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
      itemCount: items.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (_, i) => _ProductionRow(row: items[i]),
    );
  }
}

class _ProductionRow extends StatelessWidget {
  const _ProductionRow({required this.row});
  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final wc = (row['watercut_pct'] as num?)?.toDouble() ?? 0;
    final wcColor = wc > 90
        ? AppColors.dangerRed
        : (wc > 70 ? AppColors.warnOrange : AppColors.goodGreen);
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: scheme.primary.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Text(
                (row['block'] ?? '?').toString(),
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: scheme.primary,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    fmtDate(row['date']),
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      _MiniStat(
                        icon: Icons.oil_barrel_rounded,
                        text: fmtBbl(row['oil_bbl'] as num?),
                      ),
                      _MiniStat(
                        icon: Icons.water_drop_rounded,
                        text: fmtPct(wc),
                        color: wcColor,
                      ),
                      _MiniStat(
                        icon: Icons.adjust_rounded,
                        text:
                            '${row['wells_active'] ?? '—'}/${row['wells_total'] ?? '—'}',
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.icon, required this.text, this.color});
  final IconData icon;
  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final c = color ?? Theme.of(context).colorScheme.onSurfaceVariant;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: c),
        const SizedBox(width: 4),
        Text(
          text,
          style: TextStyle(
            fontSize: 12.5,
            color: c,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
