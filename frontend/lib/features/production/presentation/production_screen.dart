import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/providers/blocks_providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/zone_block_picker.dart';
import '../data/etl_repository.dart';
import '../data/production_repository.dart';
import 'production_forecast_tab.dart';

final _repoProvider = Provider<ProductionRepository>(
  (ref) => ProductionRepository(ref.watch(apiClientProvider)),
);

final _etlRepoProvider = Provider<EtlRepository>(
  (ref) => EtlRepository(ref.watch(apiClientProvider)),
);

final _dailyProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).daily(),
);

void _showExcelImport(BuildContext context, WidgetRef ref) {
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (_) => const _ExcelImportDialog(),
  );
}

class ProductionScreen extends ConsumerWidget {
  const ProductionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Production'),
          bottom: const TabBar(
            indicatorWeight: 3,
            labelStyle: TextStyle(fontWeight: FontWeight.w700),
            tabs: [
              Tab(icon: Icon(Icons.list_alt_rounded), text: 'Données'),
              Tab(icon: Icon(Icons.timeline_rounded), text: 'Prévision IA'),
            ],
          ),
          actions: [
            IconButton(
              tooltip: 'Importer un fichier Excel',
              icon: const Icon(Icons.upload_file_rounded),
              onPressed: () => _showExcelImport(context, ref),
            ),
            IconButton(
              tooltip: 'Actualiser',
              icon: const Icon(Icons.refresh_rounded),
              onPressed: () => ref.invalidate(_dailyProvider),
            ),
            const SizedBox(width: 4),
          ],
        ),
        body: const TabBarView(
          children: [_DailyDataTab(), ProductionForecastTab()],
        ),
      ),
    );
  }
}

// ----------------------------------------------------------------------------
// Tab 1 — Données journalières
// ----------------------------------------------------------------------------

class _DailyDataTab extends ConsumerWidget {
  const _DailyDataTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final daily = ref.watch(_dailyProvider);
    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab-daily',
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
          width: 420,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _Field(controller: dateCtrl, label: 'Date (YYYY-MM-DD)'),
                const ZoneBlockPicker(),
                const SizedBox(height: 12),
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
                final blockCode = ref.read(selectedBlockProvider);
                await ref.read(_repoProvider).create(
                      date: dateCtrl.text,
                      blockCode: blockCode,
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

// ----------------------------------------------------------------------------
// Excel ingestion dialog
// ----------------------------------------------------------------------------

class _ExcelImportDialog extends ConsumerStatefulWidget {
  const _ExcelImportDialog();

  @override
  ConsumerState<_ExcelImportDialog> createState() => _ExcelImportDialogState();
}

class _ExcelImportDialogState extends ConsumerState<_ExcelImportDialog> {
  PlatformFile? _file;
  bool _uploading = false;
  Map<String, dynamic>? _result;
  String? _error;

  Future<void> _pickFile() async {
    final res = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['xlsx', 'xls'],
      withData: true,
    );
    if (res == null || res.files.isEmpty) return;
    setState(() {
      _file = res.files.first;
      _error = null;
      _result = null;
    });
  }

  Future<void> _upload() async {
    if (_file == null || _file!.bytes == null) return;
    setState(() {
      _uploading = true;
      _error = null;
    });
    try {
      final r = await ref.read(_etlRepoProvider).ingestExcel(
            filename: _file!.name,
            bytes: _file!.bytes!,
            label:
                'ui-${DateTime.now().toIso8601String().replaceAll(":", "").substring(0, 17)}',
          );
      setState(() => _result = r);
      ref.invalidate(_dailyProvider);
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final bytes = _file?.bytes;
    return AlertDialog(
      title: const Text('Importer un fichier Excel'),
      content: SizedBox(
        width: 460,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(AppRadii.md),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Le fichier doit contenir une feuille « Prod YOM '
                      'BlocsFaillés X, Y et Z » avec les colonnes Date, '
                      'Production huile/eau, Watercut, Puits totaux et actifs.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: _uploading ? null : _pickFile,
              icon: const Icon(Icons.attach_file_rounded),
              label: Text(_file == null
                  ? 'Choisir un fichier .xlsx'
                  : '${_file!.name}'
                      ' (${((bytes?.length ?? 0) / 1024).toStringAsFixed(0)} ko)'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: scheme.errorContainer.withValues(alpha: 0.6),
                  borderRadius: BorderRadius.circular(AppRadii.md),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, size: 18, color: scheme.error),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _error!,
                        style: TextStyle(color: scheme.onErrorContainer),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (_result != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.goodGreen.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(AppRadii.md),
                  border:
                      Border.all(color: AppColors.goodGreen.withValues(alpha: 0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.check_circle_rounded,
                            color: AppColors.goodGreen, size: 18),
                        SizedBox(width: 8),
                        Text(
                          'Ingestion terminée',
                          style: TextStyle(
                            color: AppColors.goodGreen,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${_result!["rows_processed"] ?? 0} lignes ajoutées · '
                      '${_result!["rows_skipped"] ?? 0} ignorées · '
                      '${_result!["rows_failed"] ?? 0} en erreur',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _uploading ? null : () => Navigator.pop(context),
          child: Text(_result != null ? 'Fermer' : 'Annuler'),
        ),
        FilledButton.icon(
          onPressed: (_file == null || _uploading || _result != null)
              ? null
              : _upload,
          icon: _uploading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.cloud_upload_rounded),
          label: Text(_uploading ? 'Envoi en cours…' : 'Importer'),
        ),
      ],
    );
  }
}
