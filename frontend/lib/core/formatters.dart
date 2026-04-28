import 'package:intl/intl.dart';

final _frNum = NumberFormat.decimalPattern('fr');
final _frCompact = NumberFormat.compactLong(locale: 'fr');
final _frDate = DateFormat('d MMM y', 'fr_FR');
final _frDateShort = DateFormat('d/M/y', 'fr_FR');

String fmtNum(num? v, {int? decimals}) {
  if (v == null) return '—';
  if (decimals != null) {
    final f = NumberFormat.decimalPatternDigits(
      locale: 'fr',
      decimalDigits: decimals,
    );
    return f.format(v);
  }
  return _frNum.format(v);
}

String fmtCompact(num? v) {
  if (v == null) return '—';
  if (v.abs() < 1000) return _frNum.format(v);
  return _frCompact.format(v);
}

String fmtPct(num? v, {int decimals = 1}) {
  if (v == null) return '—';
  return '${v.toStringAsFixed(decimals).replaceAll('.', ',')} %';
}

String fmtBbl(num? v, {bool compact = false}) {
  if (v == null) return '—';
  return compact ? '${fmtCompact(v)} bbl' : '${fmtNum(v, decimals: 0)} bbl';
}

String fmtBblPerDay(num? v) =>
    v == null ? '—' : '${fmtNum(v, decimals: 0)} bbl/j';

String fmtDate(dynamic v) {
  if (v == null) return '—';
  final d = v is DateTime ? v : DateTime.tryParse(v.toString());
  return d == null ? '—' : _frDate.format(d);
}

String fmtDateShort(dynamic v) {
  if (v == null) return '—';
  final d = v is DateTime ? v : DateTime.tryParse(v.toString());
  return d == null ? '—' : _frDateShort.format(d);
}

String fmtDelta(num? v) {
  if (v == null) return '—';
  final sign = v >= 0 ? '+' : '';
  return '$sign${v.toStringAsFixed(1).replaceAll('.', ',')} %';
}
