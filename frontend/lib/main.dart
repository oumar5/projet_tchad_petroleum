import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router.dart';

void main() {
  runApp(const ProviderScope(child: SmartBarrelApp()));
}

class SmartBarrelApp extends ConsumerWidget {
  const SmartBarrelApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'SmartBarrel',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1F77B4)),
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
