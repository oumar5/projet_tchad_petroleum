import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../dashboard/presentation/dashboard_screen.dart';
import '../../forecast/presentation/forecast_screen.dart';
import '../../maintenance/presentation/maintenance_screen.dart';
import '../../production/presentation/production_screen.dart';
import '../../water/presentation/water_screen.dart';
import '../auth_controller.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _index = 0;

  static const _screens = [
    DashboardScreen(),
    ProductionScreen(),
    MaintenanceScreen(),
    ForecastScreen(),
    WaterScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_index],
      drawer: Drawer(
        child: ListView(children: [
          DrawerHeader(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('SmartBarrel',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(ref.watch(authControllerProvider).user?['email'] ?? '—'),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Déconnexion'),
            onTap: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.list_alt), label: 'Production'),
          NavigationDestination(icon: Icon(Icons.build), label: 'Maintenance'),
          NavigationDestination(icon: Icon(Icons.timeline), label: 'Prévision'),
          NavigationDestination(icon: Icon(Icons.water_drop), label: 'Injection'),
        ],
      ),
    );
  }
}
