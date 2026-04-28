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
import '../../../core/widgets/kpi_card.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/zone_block_picker.dart';
import '../data/maintenance_repository.dart';

const _kFailuresKey = 'maintenance.failures';
const _kInterventionsKey = 'maintenance.interventions';

final _repoProvider = Provider<MaintenanceRepository>(
  (ref) => MaintenanceRepository(ref.watch(apiClientProvider)),
);

final _failuresProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final r = await ref.watch(_repoProvider).failuresCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kFailuresKey, CacheStatus.fromResult(r));
    return r.data;
  },
);

final _interventionsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final r = await ref.watch(_repoProvider).interventionsCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kInterventionsKey, CacheStatus.fromResult(r));
    return r.data;
  },
);

class MaintenanceScreen extends ConsumerWidget {
  const MaintenanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Maintenance'),
          bottom: const TabBar(
            indicatorWeight: 3,
            labelStyle: TextStyle(fontWeight: FontWeight.w700),
            isScrollable: true,
            tabs: [
              Tab(icon: Icon(Icons.psychology_alt_rounded), text: 'Risque ML'),
              Tab(icon: Icon(Icons.warning_amber_rounded), text: 'Pannes'),
              Tab(icon: Icon(Icons.build_circle_rounded), text: 'Interventions'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [_RiskTab(), _FailuresTab(), _InterventionsTab()],
        ),
      ),
    );
  }
}

const _severityMap = {
  'low': ('Faible', AppColors.tealAccent),
  'medium': ('Moyenne', AppColors.warnOrange),
  'high': ('Élevée', AppColors.dangerRed),
  'critical': ('Critique', Color(0xFF8E44AD)),
};

// ----------------------------------------------------------------------------
// Tab 1 — ML risk prediction
// ----------------------------------------------------------------------------

class _RiskTab extends ConsumerStatefulWidget {
  const _RiskTab();

  @override
  ConsumerState<_RiskTab> createState() => _RiskTabState();
}

class _RiskTabState extends ConsumerState<_RiskTab> {
  int _horizon = 7;
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _run());
  }

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final block = ref.read(selectedBlockProvider);
      final r = await ref.read(_repoProvider).predictRisk(
            block: block,
            horizonDays: _horizon,
          );
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Paramètres',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 16),
                const ZoneBlockPicker(),
                const SizedBox(height: 12),
                LayoutBuilder(
                  builder: (ctx, c) {
                    final stack = c.maxWidth < 480;
                    final left = DropdownButtonFormField<int>(
                      initialValue: _horizon,
                      decoration: const InputDecoration(
                        labelText: 'Horizon (jours)',
                        prefixIcon: Icon(Icons.event_repeat_rounded),
                      ),
                      items: [3, 7, 14, 30]
                          .map((d) => DropdownMenuItem(
                              value: d, child: Text('$d jours')))
                          .toList(),
                      onChanged: (v) => setState(() => _horizon = v ?? 7),
                    );
                    final right = const SizedBox.shrink();
                    if (stack) {
                      return Column(children: [
                        left,
                        const SizedBox(height: 12),
                        right,
                      ]);
                    }
                    return Row(children: [
                      Expanded(child: left),
                      const SizedBox(width: 12),
                      Expanded(child: right),
                    ]);
                  },
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _loading ? null : _run,
                  icon: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.online_prediction_rounded),
                  label: Text(_loading
                      ? 'Calcul…'
                      : 'Évaluer le risque de panne'),
                ),
              ],
            ),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Card(
            color: scheme.errorContainer.withValues(alpha: 0.6),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: scheme.error),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: scheme.onErrorContainer,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 20),
        if (_result == null && _error == null && !_loading)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 40),
            child: EmptyState(
              icon: Icons.psychology_alt_rounded,
              title: 'Aucune analyse ML disponible',
              subtitle:
                  'Sélectionne un bloc et un horizon pour obtenir le risque.',
            ),
          )
        else if (_result != null)
          _RiskResult(result: _result!),
      ],
    );
  }
}

class _RiskResult extends StatelessWidget {
  const _RiskResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final preds = result['predictions'];
    final first = preds is List && preds.isNotEmpty
        ? Map<String, dynamic>.from(preds.first as Map)
        : <String, dynamic>{};

    final maxRisk = (first['max_failure_risk'] as num?)?.toDouble() ?? 0;
    final avgRisk = (first['avg_failure_risk_30d'] as num?)?.toDouble() ?? 0;
    final level = (first['risk_level'] ?? 'low').toString();
    final block = (first['block'] ?? '—').toString();
    final horizon = (first['horizon_days'] ?? '').toString();
    final asOf = first['as_of']?.toString();
    final confidence = (result['confidence'] as num?)?.toDouble();

    final modelMap = result['model'];
    final modelName = modelMap is Map
        ? '${modelMap['name'] ?? '—'} ${modelMap['version'] ?? ''}'
        : '—';

    final entry = _severityMap[level] ?? ('Inconnu', AppColors.tealAccent);
    final color = entry.$2;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Bloc $block · horizon $horizon jours',
          subtitle: 'Modèle : $modelName${asOf != null ? " · données au ${fmtDate(asOf)}" : ""}',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                _RiskGauge(value: maxRisk, color: color),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    'Niveau ${entry.$1.toLowerCase()}',
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w800,
                      fontSize: 13,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Risque max sur la fenêtre',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (ctx, c) {
            final w = c.maxWidth < 480 ? c.maxWidth : (c.maxWidth - 12) / 2;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Risque moyen 30j',
                    value: '${(avgRisk * 100).toStringAsFixed(1)} %',
                    icon: Icons.show_chart_rounded,
                    iconColor: color,
                  ),
                ),
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Confiance modèle',
                    value: confidence == null
                        ? '—'
                        : '${(confidence * 100).toStringAsFixed(0)} %',
                    icon: Icons.verified_rounded,
                    iconColor: AppColors.goodGreen,
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.lightbulb_outline_rounded,
                    color: AppColors.goldAmber, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _recommendation(level),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  String _recommendation(String level) {
    switch (level) {
      case 'high':
        return 'Risque élevé : programmer une inspection préventive sous 48 h '
            'et préparer les pièces de rechange critiques.';
      case 'medium':
        return 'Risque modéré : renforcer la surveillance et planifier '
            'une intervention dans les 7 jours.';
      default:
        return 'Risque faible : poursuivre la maintenance planifiée habituelle.';
    }
  }
}

class _RiskGauge extends StatelessWidget {
  const _RiskGauge({required this.value, required this.color});
  final double value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final pct = (value * 100).clamp(0, 100).toDouble();
    return Column(
      children: [
        SizedBox(
          width: 160,
          height: 160,
          child: Stack(
            alignment: Alignment.center,
            children: [
              SizedBox.expand(
                child: CircularProgressIndicator(
                  value: 1,
                  strokeWidth: 14,
                  valueColor: AlwaysStoppedAnimation(
                    Theme.of(context).colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
              SizedBox.expand(
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: value.clamp(0.0, 1.0)),
                  duration: const Duration(milliseconds: 700),
                  curve: Curves.easeOutCubic,
                  builder: (_, v, _) => CircularProgressIndicator(
                    value: v,
                    strokeWidth: 14,
                    valueColor: AlwaysStoppedAnimation(color),
                    strokeCap: StrokeCap.round,
                  ),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${pct.toStringAsFixed(1)}%',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'risque',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ----------------------------------------------------------------------------
// Tab 2 — Pannes (existing)
// ----------------------------------------------------------------------------

class _FailuresTab extends ConsumerWidget {
  const _FailuresTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final failures = ref.watch(_failuresProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab-failure',
        onPressed: () => _showDeclareFailureDialog(context, ref),
        icon: const Icon(Icons.add_alert_rounded),
        label: const Text('Déclarer une panne'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(_failuresProvider),
        child: failures.when(
          loading: () => const _LoadingList(),
          error: (e, _) => ErrorState(
            error: e,
            onRetry: () => ref.invalidate(_failuresProvider),
          ),
          data: (items) {
            if (items.isEmpty) {
              return EmptyState(
                icon: Icons.health_and_safety_outlined,
                title: 'Aucune panne déclarée',
                subtitle:
                    'Aucun incident à signaler.\n\nDéclare une panne dès qu’un technicien remonte un défaut '
                    'pour qu’elle soit suivie ici.',
                action: FilledButton.icon(
                  onPressed: () => _showDeclareFailureDialog(context, ref),
                  icon: const Icon(Icons.add_alert_rounded),
                  label: const Text('Déclarer une panne'),
                ),
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 88),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _FailureCard(row: items[i]),
            );
          },
        ),
      ),
    );
  }
}

class _FailureCard extends ConsumerWidget {
  const _FailureCard({required this.row});
  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    final sev = (row['severity'] ?? 'low').toString();
    final entry = _severityMap[sev] ?? ('Inconnu', scheme.outline);
    final status = (row['status'] ?? 'pending').toString();
    final resolved = status == 'resolved' || row['resolved_at'] != null;
    final id = row['id']?.toString();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 72,
              decoration: BoxDecoration(
                color: entry.$2,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${row['block'] ?? '—'}'
                          '${row['well_code'] != null ? ' · ${row['well_code']}' : ''}'
                          ' · ${row['failure_type'] ?? '—'}',
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: entry.$2.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          entry.$1,
                          style: TextStyle(
                            color: entry.$2,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        fmtDate(row['notification_date']),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(width: 10),
                      _StatusChip(status: status),
                    ],
                  ),
                  if (row['description'] != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      row['description'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 4),
            if (resolved)
              const Icon(Icons.check_circle_rounded,
                  color: AppColors.goodGreen, size: 24)
            else
              Icon(Icons.pending_rounded,
                  color: scheme.onSurfaceVariant, size: 22),
            if (id != null)
              PopupMenuButton<String>(
                tooltip: 'Actions',
                icon: const Icon(Icons.more_vert_rounded),
                onSelected: (action) =>
                    _onFailureAction(context, ref, id, action),
                itemBuilder: (_) => [
                  if (status != 'in_progress' && status != 'resolved')
                    const PopupMenuItem(
                      value: 'in_progress',
                      child: ListTile(
                        leading: Icon(Icons.play_arrow_rounded),
                        title: Text('Marquer en cours'),
                      ),
                    ),
                  if (status != 'resolved')
                    const PopupMenuItem(
                      value: 'resolved',
                      child: ListTile(
                        leading: Icon(Icons.check_circle_outline),
                        title: Text('Marquer résolu'),
                      ),
                    ),
                  if (status == 'resolved')
                    const PopupMenuItem(
                      value: 'reopen',
                      child: ListTile(
                        leading: Icon(Icons.replay_rounded),
                        title: Text('Rouvrir'),
                      ),
                    ),
                  const PopupMenuItem(
                    value: 'attach',
                    child: ListTile(
                      leading: Icon(Icons.attach_file_rounded),
                      title: Text('Ajouter une photo'),
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'intervention',
                    child: ListTile(
                      leading: Icon(Icons.build_rounded),
                      title: Text('Ajouter une intervention'),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;
  static const _labels = {
    'pending': ('En attente', Icons.schedule_rounded),
    'in_progress': ('En cours', Icons.play_arrow_rounded),
    'resolved': ('Résolu', Icons.check_circle_rounded),
    'cancelled': ('Annulé', Icons.cancel_rounded),
  };
  static const _colors = {
    'pending': AppColors.warnOrange,
    'in_progress': AppColors.tealAccent,
    'resolved': AppColors.goodGreen,
    'cancelled': Colors.grey,
  };
  @override
  Widget build(BuildContext context) {
    final entry = _labels[status] ?? ('Inconnu', Icons.help_outline);
    final color = _colors[status] ?? Colors.grey;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(entry.$2, color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            entry.$1,
            style: TextStyle(
              color: color, fontSize: 10.5, fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

Future<void> _onFailureAction(
    BuildContext context, WidgetRef ref, String id, String action) async {
  final repo = ref.read(_repoProvider);
  try {
    switch (action) {
      case 'in_progress':
        await repo.updateFailure(failureId: id, status: 'in_progress');
        break;
      case 'resolved':
        await repo.updateFailure(failureId: id, status: 'resolved');
        break;
      case 'reopen':
        await repo.updateFailure(failureId: id, status: 'pending');
        break;
      case 'attach':
        if (context.mounted) await _pickAndUploadPhoto(context, ref, id);
        return;
      case 'intervention':
        if (context.mounted) {
          await _showInterventionDialog(context, ref, failureId: id);
        }
        return;
    }
    ref.invalidate(_failuresProvider);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Mis à jour')),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(prettyError(e))),
      );
    }
  }
}

Future<void> _pickAndUploadPhoto(
    BuildContext context, WidgetRef ref, String failureId) async {
  final picked = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp', 'pdf'],
    withData: true,
  );
  if (picked == null || picked.files.isEmpty) return;
  final f = picked.files.single;
  if (f.bytes == null || f.bytes!.isEmpty) return;
  final ext = (f.extension ?? '').toLowerCase();
  final mime = switch (ext) {
    'jpg' || 'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    'webp' => 'image/webp',
    'pdf' => 'application/pdf',
    _ => 'application/octet-stream',
  };
  try {
    await ref.read(_repoProvider).uploadFailureAttachment(
          failureId: failureId,
          filename: f.name,
          bytes: f.bytes!,
          mimeType: mime,
        );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Photo attachée')),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(prettyError(e))),
      );
    }
  }
}

Future<void> _showDeclareFailureDialog(
    BuildContext context, WidgetRef ref) async {
  final dateCtrl = TextEditingController(
      text: DateTime.now().toIso8601String().substring(0, 10));
  final wellCtrl = TextEditingController();
  final descCtrl = TextEditingController();
  final etaCtrl = TextEditingController();
  String type = 'ESP_motor';
  String severity = 'medium';

  await showDialog<void>(
    context: context,
    builder: (dlgCtx) => StatefulBuilder(
      builder: (sbCtx, setLocal) => AlertDialog(
        title: const Text('Déclarer une panne'),
        content: SizedBox(
          width: 460,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: dateCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Date (YYYY-MM-DD)',
                  ),
                ),
                const SizedBox(height: 12),
                const ZoneBlockPicker(),
                const SizedBox(height: 12),
                TextField(
                  controller: wellCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Code puits (optionnel, ex: X-04)',
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Type de panne'),
                  items: const [
                    DropdownMenuItem(value: 'ESP_motor', child: Text('Moteur ESP')),
                    DropdownMenuItem(value: 'ESP_pump', child: Text('Pompe ESP')),
                    DropdownMenuItem(value: 'cable', child: Text('Câble')),
                    DropdownMenuItem(value: 'sensor', child: Text('Capteur')),
                    DropdownMenuItem(value: 'flowline', child: Text('Conduite')),
                    DropdownMenuItem(value: 'other', child: Text('Autre')),
                  ],
                  onChanged: (v) => setLocal(() => type = v ?? type),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: severity,
                  decoration: const InputDecoration(labelText: 'Sévérité'),
                  items: const [
                    DropdownMenuItem(value: 'low', child: Text('Basse')),
                    DropdownMenuItem(value: 'medium', child: Text('Moyenne')),
                    DropdownMenuItem(value: 'high', child: Text('Haute')),
                    DropdownMenuItem(value: 'critical', child: Text('Critique')),
                  ],
                  onChanged: (v) => setLocal(() => severity = v ?? severity),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: etaCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Durée estimée (heures)',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: descCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Description',
                    hintText: 'Symptômes observés, contexte…',
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dlgCtx),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () async {
              try {
                final blockCode = ref.read(selectedBlockProvider);
                final eta = int.tryParse(etaCtrl.text);
                await ref.read(_repoProvider).reportFailure(
                      date: dateCtrl.text,
                      block: blockCode,
                      wellCode: wellCtrl.text.isEmpty ? null : wellCtrl.text,
                      type: type,
                      severity: severity,
                      description:
                          descCtrl.text.isEmpty ? null : descCtrl.text,
                      estimatedDurationH: eta,
                    );
                if (dlgCtx.mounted) Navigator.pop(dlgCtx);
                ref.invalidate(_failuresProvider);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Panne déclarée')),
                  );
                }
              } catch (e) {
                if (dlgCtx.mounted) {
                  ScaffoldMessenger.of(dlgCtx).showSnackBar(
                    SnackBar(content: Text(prettyError(e))),
                  );
                }
              }
            },
            child: const Text('Déclarer'),
          ),
        ],
      ),
    ),
  );
}

Future<void> _showInterventionDialog(
  BuildContext context,
  WidgetRef ref, {
  String? failureId,
}) async {
  final dateCtrl = TextEditingController(
      text: DateTime.now().toIso8601String().substring(0, 10));
  final durationCtrl = TextEditingController();
  final costCtrl = TextEditingController();
  final notesCtrl = TextEditingController();
  String type = 'inspection';
  String result = 'success';

  await showDialog<void>(
    context: context,
    builder: (dlgCtx) => StatefulBuilder(
      builder: (sbCtx, setLocal) => AlertDialog(
        title: Text(failureId != null
            ? 'Intervention pour cette panne'
            : 'Nouvelle intervention'),
        content: SizedBox(
          width: 440,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: dateCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Date (YYYY-MM-DD)',
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: const [
                    DropdownMenuItem(value: 'inspection', child: Text('Inspection')),
                    DropdownMenuItem(value: 'repair', child: Text('Réparation')),
                    DropdownMenuItem(value: 'replacement', child: Text('Remplacement')),
                    DropdownMenuItem(value: 'cleaning', child: Text('Nettoyage')),
                  ],
                  onChanged: (v) => setLocal(() => type = v ?? type),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: durationCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Durée (heures)',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: costCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Coût (USD)',
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: result,
                  decoration: const InputDecoration(labelText: 'Résultat'),
                  items: const [
                    DropdownMenuItem(value: 'success', child: Text('Succès')),
                    DropdownMenuItem(value: 'partial', child: Text('Partiel')),
                    DropdownMenuItem(value: 'failed', child: Text('Échec')),
                  ],
                  onChanged: (v) => setLocal(() => result = v ?? result),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesCtrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Notes',
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dlgCtx),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () async {
              try {
                await ref.read(_repoProvider).createIntervention(
                      date: dateCtrl.text,
                      type: type,
                      failureId: failureId,
                      durationH: double.tryParse(durationCtrl.text),
                      cost: double.tryParse(costCtrl.text),
                      result: result,
                      notes: notesCtrl.text.isEmpty ? null : notesCtrl.text,
                    );
                if (dlgCtx.mounted) Navigator.pop(dlgCtx);
                ref.invalidate(_interventionsProvider);
                if (failureId != null) ref.invalidate(_failuresProvider);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Intervention enregistrée')),
                  );
                }
              } catch (e) {
                if (dlgCtx.mounted) {
                  ScaffoldMessenger.of(dlgCtx).showSnackBar(
                    SnackBar(content: Text(prettyError(e))),
                  );
                }
              }
            },
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    ),
  );
}

// ----------------------------------------------------------------------------
// Tab 3 — Interventions (existing)
// ----------------------------------------------------------------------------

class _InterventionsTab extends ConsumerWidget {
  const _InterventionsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(_interventionsProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton.extended(
        heroTag: 'fab-intervention',
        onPressed: () => _showInterventionDialog(context, ref),
        icon: const Icon(Icons.build_rounded),
        label: const Text('Nouvelle intervention'),
      ),
      body: RefreshIndicator(
      onRefresh: () async => ref.invalidate(_interventionsProvider),
      child: items.when(
        loading: () => const _LoadingList(),
        error: (e, _) => ErrorState(
          error: e,
          onRetry: () => ref.invalidate(_interventionsProvider),
        ),
        data: (rows) {
          if (rows.isEmpty) {
            return const EmptyState(
              icon: Icons.build_outlined,
              title: 'Aucune intervention enregistrée',
              subtitle:
                  'Dès qu’une équipe déclare une intervention sur le terrain '
                  '(remplacement de pompe, nettoyage, contrôle…), elle s’affichera ici '
                  'avec sa durée et son coût.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final r = rows[i];
              return Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 6),
                  leading: CircleAvatar(
                    backgroundColor:
                        AppColors.tealAccent.withValues(alpha: 0.15),
                    child: const Icon(Icons.build_rounded,
                        color: AppColors.tealAccent),
                  ),
                  title: Text(
                    (r['intervention_type'] ?? '—').toString(),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(fmtDate(r['intervention_date'])),
                  trailing: Text(
                    '${r['duration_h'] ?? '—'} h',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              );
            },
          );
        },
      ),
      ),
    );
  }
}

class _LoadingList extends StatelessWidget {
  const _LoadingList();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (_, _) => const Skeleton(height: 80, radius: 12),
    );
  }
}
