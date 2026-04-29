import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/offline/cache_status.dart';
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

const _kFeatureKey = 'production.daily';

final _repoProvider = Provider<ProductionRepository>(
  (ref) => ProductionRepository(ref.watch(apiClientProvider)),
);

final _etlRepoProvider = Provider<EtlRepository>(
  (ref) => EtlRepository(ref.watch(apiClientProvider)),
);

final _dailyProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final result = await ref.watch(_repoProvider).dailyCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kFeatureKey, CacheStatus.fromResult(result));
    return result.data;
  },
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
                icon: Icons.cloud_upload_outlined,
                title: 'Démarrons en important vos données',
                subtitle:
                    'Aucune saisie pour le moment.\n\n• Importez un fichier Excel pour charger l’historique en quelques secondes.\n• Ou ajoutez manuellement une journée de production.',
                action: Wrap(
                  spacing: 12,
                  runSpacing: 8,
                  alignment: WrapAlignment.center,
                  children: [
                    FilledButton.icon(
                      onPressed: () => _showExcelImport(context, ref),
                      icon: const Icon(Icons.upload_file_rounded),
                      label: const Text('Importer Excel'),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _showCreateDialog(context, ref),
                      icon: const Icon(Icons.add_rounded),
                      label: const Text('Saisie manuelle'),
                    ),
                  ],
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

/// Three-step wizard:
///   1. Pick a file
///   2. Show the per-sheet analysis returned by /inspect/excel — user picks which to ingest
///   3. Show ingestion result
class _ExcelImportDialog extends ConsumerStatefulWidget {
  const _ExcelImportDialog();

  @override
  ConsumerState<_ExcelImportDialog> createState() => _ExcelImportDialogState();
}

enum _WizardStep { pickFile, review, result }

class _ExcelImportDialogState extends ConsumerState<_ExcelImportDialog> {
  PlatformFile? _file;
  Map<String, dynamic>? _inspect;
  Map<String, dynamic>? _result;
  final Set<String> _selected = {};
  String? _error;
  bool _busy = false;
  _WizardStep _step = _WizardStep.pickFile;

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
      _inspect = null;
      _result = null;
      _selected.clear();
    });
  }

  Future<void> _runInspect() async {
    if (_file == null || _file!.bytes == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final r = await ref.read(_etlRepoProvider).inspectExcel(
            filename: _file!.name,
            bytes: _file!.bytes!,
          );
      // Pre-select every sheet that the backend marks as ready=true
      final preselected = <String>{};
      for (final s in (r['sheets'] as List)) {
        final m = Map<String, dynamic>.from(s as Map);
        if (m['ready'] == true) {
          preselected.add(m['detected_kind'] as String);
        }
      }
      setState(() {
        _inspect = r;
        _selected.addAll(preselected);
        _step = _WizardStep.review;
      });
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _runIngest() async {
    if (_inspect == null || _selected.isEmpty) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final r = await ref.read(_etlRepoProvider).ingestSelective(
            snapshotId: _inspect!['snapshot_id'] as String,
            sheets: _selected.toList(),
          );
      setState(() {
        _result = r;
        _step = _WizardStep.result;
      });
      ref.invalidate(_dailyProvider);
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.cloud_upload_rounded),
          const SizedBox(width: 8),
          Expanded(child: Text(_titleForStep())),
          _StepBadge(step: _step),
        ],
      ),
      content: SizedBox(
        width: 640,
        child: SingleChildScrollView(child: _bodyForStep()),
      ),
      actions: _actionsForStep(),
    );
  }

  String _titleForStep() => switch (_step) {
        _WizardStep.pickFile => 'Importer un fichier Excel',
        _WizardStep.review => 'Sélectionner les onglets à importer',
        _WizardStep.result => 'Résultat de l\'import',
      };

  Widget _bodyForStep() {
    switch (_step) {
      case _WizardStep.pickFile:
        return _StepPickFile(
          file: _file,
          error: _error,
          onPick: _busy ? null : _pickFile,
        );
      case _WizardStep.review:
        return _StepReview(
          inspect: _inspect!,
          selected: _selected,
          error: _error,
          onToggle: _busy
              ? null
              : (kind, on) => setState(() {
                    if (on) {
                      _selected.add(kind);
                    } else {
                      _selected.remove(kind);
                    }
                  }),
        );
      case _WizardStep.result:
        return _StepResult(result: _result!);
    }
  }

  List<Widget> _actionsForStep() {
    switch (_step) {
      case _WizardStep.pickFile:
        return [
          TextButton(
            onPressed: _busy ? null : () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          FilledButton.icon(
            onPressed: (_file == null || _busy) ? null : _runInspect,
            icon: _busy
                ? const SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.search_rounded),
            label: Text(_busy ? 'Analyse…' : 'Analyser'),
          ),
        ];
      case _WizardStep.review:
        return [
          TextButton(
            onPressed: _busy ? null : () => setState(() => _step = _WizardStep.pickFile),
            child: const Text('Retour'),
          ),
          FilledButton.icon(
            onPressed: (_busy || _selected.isEmpty) ? null : _runIngest,
            icon: _busy
                ? const SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.check_rounded),
            label: Text(_busy
                ? 'Importation…'
                : 'Importer ${_selected.length} onglet${_selected.length > 1 ? 's' : ''}'),
          ),
        ];
      case _WizardStep.result:
        return [
          FilledButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.check_rounded),
            label: const Text('Terminer'),
          ),
        ];
    }
  }
}

class _StepBadge extends StatelessWidget {
  const _StepBadge({required this.step});
  final _WizardStep step;
  @override
  Widget build(BuildContext context) {
    final n = switch (step) {
      _WizardStep.pickFile => '1/3',
      _WizardStep.review => '2/3',
      _WizardStep.result => '3/3',
    };
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: scheme.primaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        n,
        style: TextStyle(
          color: scheme.onPrimaryContainer,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _StepPickFile extends StatelessWidget {
  const _StepPickFile({required this.file, required this.error, required this.onPick});
  final PlatformFile? file;
  final String? error;
  final VoidCallback? onPick;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHighest.withValues(alpha: 0.4),
            borderRadius: BorderRadius.circular(AppRadii.md),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.info_outline_rounded, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'L\'analyse va lire automatiquement chaque onglet de votre fichier '
                  'Excel et vous montrer ce qui sera importé. Aucune donnée n\'est '
                  'écrite tant que vous n\'avez pas validé l\'étape 2.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: onPick,
          icon: const Icon(Icons.attach_file_rounded),
          label: Text(file == null
              ? 'Choisir un fichier .xlsx'
              : '${file!.name} (${((file!.bytes?.length ?? 0) / 1024).toStringAsFixed(0)} Ko)'),
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          _ErrorBox(message: error!),
        ],
      ],
    );
  }
}

class _StepReview extends StatelessWidget {
  const _StepReview({
    required this.inspect,
    required this.selected,
    required this.error,
    required this.onToggle,
  });
  final Map<String, dynamic> inspect;
  final Set<String> selected;
  final String? error;
  final void Function(String kind, bool on)? onToggle;

  @override
  Widget build(BuildContext context) {
    final sheets = (inspect['sheets'] as List).cast<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
    final filename = inspect['filename'] ?? 'fichier';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Analyse de « $filename »',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 4),
        Text(
          '${sheets.length} onglet${sheets.length > 1 ? 's' : ''} détecté${sheets.length > 1 ? 's' : ''}. '
          'Cochez ceux à importer. Les types non encore supportés sont marqués comme tels.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 12),
        for (final s in sheets) _SheetRow(sheet: s, selected: selected, onToggle: onToggle),
        if (error != null) ...[
          const SizedBox(height: 12),
          _ErrorBox(message: error!),
        ],
      ],
    );
  }
}

class _SheetRow extends StatelessWidget {
  const _SheetRow({
    required this.sheet,
    required this.selected,
    required this.onToggle,
  });
  final Map<String, dynamic> sheet;
  final Set<String> selected;
  final void Function(String kind, bool on)? onToggle;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final kind = (sheet['detected_kind'] ?? 'unknown').toString();
    final ready = sheet['ready'] == true;
    final rows = sheet['rows'] ?? 0;
    final target = (sheet['target_table'] ?? '—').toString();
    final granularity = (sheet['granularity'] ?? 'day').toString();
    final warnings =
        (sheet['warnings'] as List?)?.cast<String>() ?? const <String>[];
    final canSelect = ready;
    final isSelected = selected.contains(kind);

    final (statusIcon, statusColor) = _statusIcon(kind, ready);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        border: Border.all(
          color: isSelected
              ? scheme.primary
              : scheme.outlineVariant.withValues(alpha: 0.5),
          width: isSelected ? 1.5 : 1,
        ),
        borderRadius: BorderRadius.circular(AppRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Checkbox(
              value: isSelected,
              onChanged: canSelect && onToggle != null
                  ? (v) => onToggle!(kind, v ?? false)
                  : null,
            ),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(statusIcon, color: statusColor, size: 18),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          (sheet['name'] ?? '').toString(),
                          style: const TextStyle(fontWeight: FontWeight.w800),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainerHighest
                              .withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          '$rows lignes',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      _Pill(
                        text: kind,
                        color: ready
                            ? AppColors.goodGreen
                            : (kind == 'unknown'
                                ? scheme.error
                                : AppColors.warnOrange),
                      ),
                      _Pill(text: 'cible: $target', color: scheme.primary),
                      _Pill(
                        text: granularity == 'minute'
                            ? '⏱ minute'
                            : (granularity == 'metadata'
                                ? '🏷 méta'
                                : '📅 jour'),
                        color: scheme.tertiary,
                      ),
                    ],
                  ),
                  if (warnings.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    for (final w in warnings)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.warning_amber_rounded,
                                size: 14, color: AppColors.warnOrange),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                w,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  (IconData, Color) _statusIcon(String kind, bool ready) {
    if (ready) return (Icons.check_circle_rounded, AppColors.goodGreen);
    if (kind == 'unknown') return (Icons.help_outline_rounded, Colors.grey);
    return (Icons.hourglass_top_rounded, AppColors.warnOrange);
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text, required this.color});
  final String text;
  final Color color;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _StepResult extends StatelessWidget {
  const _StepResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final totals = Map<String, dynamic>.from(result['totals'] ?? {});
    final sheets = (result['sheets'] as List).cast<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
    final isOk = (result['status'] ?? 'success') == 'success';
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: (isOk ? AppColors.goodGreen : scheme.error)
                .withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(AppRadii.md),
            border: Border.all(
              color: (isOk ? AppColors.goodGreen : scheme.error)
                  .withValues(alpha: 0.4),
            ),
          ),
          child: Row(
            children: [
              Icon(
                isOk ? Icons.check_circle_rounded : Icons.error_outline_rounded,
                color: isOk ? AppColors.goodGreen : scheme.error,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isOk ? 'Import terminé' : 'Import partiel',
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        color: isOk ? AppColors.goodGreen : scheme.error,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${totals['rows_processed'] ?? 0} ajoutées · '
                      '${totals['rows_skipped'] ?? 0} ignorées · '
                      '${totals['rows_failed'] ?? 0} en erreur',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        for (final s in sheets) _ResultRow(sheet: s),
      ],
    );
  }
}

class _ResultRow extends StatelessWidget {
  const _ResultRow({required this.sheet});
  final Map<String, dynamic> sheet;
  @override
  Widget build(BuildContext context) {
    final status = (sheet['status'] ?? '').toString();
    final color = switch (status) {
      'success' => AppColors.goodGreen,
      'failed' => Theme.of(context).colorScheme.error,
      _ => Colors.grey,
    };
    final icon = switch (status) {
      'success' => Icons.check_circle_rounded,
      'failed' => Icons.error_outline_rounded,
      _ => Icons.skip_next_rounded,
    };
    final detail = sheet['error']?.toString() ??
        sheet['reason']?.toString() ??
        '${sheet['rows_processed'] ?? 0} ajoutées · '
            '${sheet['rows_skipped'] ?? 0} ignorées · '
            '${sheet['rows_failed'] ?? 0} en erreur';
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(AppRadii.sm),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${sheet['kind']}'
                  '${sheet['sheet_name'] != null ? ' — ${sheet['sheet_name']}' : ''}',
                  style: TextStyle(fontWeight: FontWeight.w800, color: color),
                ),
                const SizedBox(height: 2),
                Text(
                  detail,
                  style: Theme.of(context).textTheme.bodySmall,
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBox extends StatelessWidget {
  const _ErrorBox({required this.message});
  final String message;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
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
              message,
              style: TextStyle(color: scheme.onErrorContainer),
            ),
          ),
        ],
      ),
    );
  }
}
