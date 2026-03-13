El archivo *estaciones.geojson* es una capa de puntos con las estaciones y sus atributos. Se puede
cargar el cualquier programa SIG (QGIS, ArcGIS...).

El campo "url_link" contiene la dirección web del hidrograma interactivo de la estación. Para poder
acceder rápidamente desde QGIS al hidrograma, añade las siguientes líneas en el campo "HTML Map Tip"
dentro de la ventana `properties>display` de la capa:

```html
<div style="font-family: sans-serif; font-size: 10px;">
  <table style="border-spacing: 0 4px;">
    <tr>
      <td style="padding-right: 10px;">Estación:</td>
      <td><b>[% title("indroea") %]</b></td>
    </tr>
    <tr>
      <td style="padding-right: 10px;">Nombre:</td>
      <td><b>[% title("lugar") %]</b></td>
    </tr>
    <tr>
      <td style="padding-right: 10px;">Río:</td>
      <td><b>[% title("rio") %]</b></td>
    </tr>
  </table>
  
  <div style="margin-top: 10px;">
    <a href="[% "url_link" %]" target="_blank" style="color: steelblue; text-decoration: none; font-weight: bold;">
      Hidrograma →
    </a>
  </div>
</div>
```

Además, tienes que activar Map Tip dentro de la barra de herramientas "Attributes Toolbar". Una vez
hechos estos pasos, al pasar el ratón por una estación surgirá un bocadillo con un acceso al 
hidrograma, que se abrirá en tu navegador.