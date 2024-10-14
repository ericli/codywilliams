package config

type Config struct {
	DataSources map[string]DataSourceConfig `yaml:"datasources"`
	Service     ServiceConfig               `yaml:"service"`
}

type DataSourceConfig struct {
	Symbols         []string `yaml:"symbols"`
	RefreshInterval string   `yaml:"refresh_interval"`
}

type ServiceConfig struct {
	BufferSize int `yaml:"buffer_size"`
}

func LoadConfig(filename string) (*Config, error) {
	// Implementation to load and parse YAML file
}
