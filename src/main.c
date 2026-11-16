#include <zephyr/kernel.h>
#include <zephyr/app_version.h>

int main(void)
{
	unsigned int n = 0;

	while (1) {
		printk("mcuboot-lab: app v%s running from slot 0, tick %u\n", APP_VERSION_STRING, n++);
		k_sleep(K_SECONDS(1));
	}
	return 0;
}
